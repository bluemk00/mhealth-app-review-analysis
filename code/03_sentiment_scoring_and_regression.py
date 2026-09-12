# -*- coding: utf-8 -*-
"""
Part 3: Zero-shot sentiment scoring + labelset evaluation + OLS regression
- Zero-shot scoring: DeBERTa-v3-large (MoritzLaurer/deberta-v3-large-zeroshot-v2.0)
- Labelset evaluation: H_norm, Avg|corr|, OOS R² (5-fold CV, random_state=42)
- OLS regression: review-level, excluding 'sentiment' dimension
- Runs for both consumer-targeted (category1) and provider-targeted (category2)

Run environment: Python venv with torch (CUDA 12.8+); see docs/setup_guide.md.
Tunable config (model, RUN_STAMP, labelsets): code/settings.py
"""

import os
import re
import numpy as np
import pandas as pd
from tqdm import tqdm
import torch
from transformers import pipeline
import statsmodels.api as sm
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Run relative to this file so ../data and ../outputs resolve regardless of cwd (matches 01).
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# ============================================================
# Config (tunable values live in code/settings.py)
# ============================================================
from settings import ZS_MODEL_ID, HYPOTHESIS_TEMPLATE, RUN_STAMP, CANDIDATES

os.makedirs(f"../outputs/anal_res_{RUN_STAMP}/", exist_ok=True)

# Minimum word count for a review to be scored (reviews shorter than this are
# skipped). Default 3, applied to the ORIGINAL review text (author track). The
# provided track sets MIN_REVIEW_WORDS=1: its corpus was already filtered on the
# original text *before* masking, so the 3-word cut must not be re-applied to the
# (shorter) masked text — otherwise masked short reviews would be dropped twice.
MIN_REVIEW_WORDS = int(os.getenv("MIN_REVIEW_WORDS", "3"))

DATASETS = [
    {
        "tag": "category1",
        "input_csv":   os.getenv("INPUT_CSV_CAT1",  f"../data/processed_{RUN_STAMP}/cleaned_reviews_of_category1.csv"),
        "results_dir": os.getenv("RESULTS_DIR_CAT1", f"../outputs/anal_res_{RUN_STAMP}/category1/"),
    },
    {
        "tag": "category2",
        "input_csv":   os.getenv("INPUT_CSV_CAT2",  f"../data/processed_{RUN_STAMP}/cleaned_reviews_of_category2.csv"),
        "results_dir": os.getenv("RESULTS_DIR_CAT2", f"../outputs/anal_res_{RUN_STAMP}/category2/"),
    },
]


# ============================================================
# Utils
# ============================================================
def safe_to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def suffixed_dir(base_dir: str, suffix: str) -> str:
    """Replace trailing number in anal_res_<N> with labelset suffix."""
    base = base_dir.rstrip("/\\")
    m = re.search(r"(.*[/\\]anal_res_)\d+$", base)
    out = f"{m.group(1)}{suffix}/" if m else f"{base}_{suffix}/"
    os.makedirs(out, exist_ok=True)
    return out

# ============================================================
# OLS helper
# ============================================================
def run_ols_and_save(results_dir: str, ols_df: pd.DataFrame, feature_cols: list, ds_tag: str = ""):
    """
    OLS regression: rating (1-5) ~ scaled factor scores [0,1].
    Saves summary (.txt) and coefficients (.csv).
    """
    use_cols = ["rating"] + feature_cols
    ols_df = ols_df.loc[:, use_cols].apply(pd.to_numeric, errors="coerce").dropna()

    # Drop zero-variance columns
    drop_zero = [c for c in feature_cols if ols_df[c].nunique() <= 1]
    if drop_zero:
        print(f"[WARN] Dropping zero-variance cols ({ds_tag}): {drop_zero}")
        ols_df = ols_df.drop(columns=drop_zero)
        feature_cols = [c for c in feature_cols if c not in drop_zero]

    if len(ols_df) < 2 or len(feature_cols) == 0:
        raise ValueError(
            f"[ERROR] Not enough data for OLS ({ds_tag}). "
            f"rows={len(ols_df)}, features={len(feature_cols)}"
        )

    X = ols_df[feature_cols]
    y = ols_df["rating"].astype(float)
    X = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y, X).fit()

    file_suffix = f"_{ds_tag}" if ds_tag else ""

    # Summary text
    sum_path = os.path.join(results_dir, f"ols_summary{file_suffix}.txt")
    with open(sum_path, "w", encoding="utf-8") as f:
        try:
            f.write(model.summary().as_text())
        except Exception as e:
            f.write(f"Summary failed: {e}\n\nCoefficients:\n{model.params.to_string()}")
    print("[SAVED]", sum_path)

    # Coefficients CSV
    coef_path = os.path.join(results_dir, f"ols_coefs{file_suffix}.csv")
    pd.DataFrame({
        "variable": model.params.index,
        "coef":     model.params.values,
        "std_err":  model.bse.values,
        "t":        model.tvalues.values,
        "p":        model.pvalues.values,
        "ci_lower": model.conf_int()[0].values,
        "ci_upper": model.conf_int()[1].values,
    }).to_csv(coef_path, index=False)
    print("[SAVED]", coef_path)

# ============================================================
# Build zero-shot classifier ONCE
# ============================================================
device = 0 if torch.cuda.is_available() else -1
clf = pipeline(
    "zero-shot-classification",
    model=ZS_MODEL_ID,
    device=device,
    hypothesis_template=HYPOTHESIS_TEMPLATE,
)
print(f"[INFO] Model loaded: {ZS_MODEL_ID} | device: {'GPU' if device == 0 else 'CPU'}")

# ============================================================
# Main loop
# ============================================================
for ds in DATASETS:
    ds_tag         = ds["tag"]
    input_csv      = ds["input_csv"]
    base_results_dir = ds["results_dir"]
    os.makedirs(base_results_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"DATASET: {ds_tag}")
    print(f"INPUT:   {input_csv}")
    print(f"OUTPUT:  {base_results_dir}")
    print(f"{'='*60}")

    # Load reviews
    df_in = pd.read_csv(input_csv)
    rows = []
    for _, row in df_in.iterrows():
        rating = row.get("score")
        txt = str(row.get("content_clean") or "").strip()
        if not txt or len(txt.split()) < MIN_REVIEW_WORDS:
            continue
        rows.append((row.get("appId", ""), rating, txt))  # appId included
    print(f"[INFO] Reviews to score: {len(rows)}")

    # Collect metrics across all labelsets for this dataset
    all_metrics = []

    for cfg in CANDIDATES:
        suffix          = cfg["suffix"]
        candidate_labels = cfg["candidate_labels"]
        paired_labels   = cfg["paired_labels"]
        new_cols        = cfg["new_cols"]

        results_dir = suffixed_dir(base_results_dir, suffix)
        os.makedirs(results_dir, exist_ok=True)
        print(f"\n--- Labelset {cfg['name']} => {results_dir} ---")

        # ── Zero-shot scoring ──────────────────────────────
        raw_records = []
        for app_id, rating, txt in tqdm(rows, desc=f"scoring ({ds_tag}|{suffix})", unit="review"):
            try:
                out = clf(txt, candidate_labels, multi_label=True)
                scores_by_label = dict(zip(out["labels"], out["scores"]))
                label_scores = [safe_to_float(scores_by_label.get(l, 0.0)) for l in candidate_labels]
            except Exception:
                label_scores = [0.0] * len(candidate_labels)
            raw_records.append([app_id, rating, txt] + label_scores)

        raw_cols = ["appID", "rating", "review"] + candidate_labels
        df = pd.DataFrame(raw_records, columns=raw_cols)

        # ── Factor scores: (pos - neg + 1) / 2  →  [0, 1] ──
        for name, (pos, neg) in zip(new_cols, paired_labels):
            df[name] = df[pos] - df[neg]

        # ── Save raw scores and factor scores ──────────────
        df[["appID", "rating", "review"] + candidate_labels].to_csv(
            os.path.join(results_dir, "scores_raw.csv"), index=False
        )
        df[["appID", "rating", "review"] + new_cols].to_csv(
            os.path.join(results_dir, "scores_with_factors.csv"), index=False
        )
        print("[SAVED] scores_raw.csv / scores_with_factors.csv")

        # ── OLS (exclude sentiment) ────────────────────────
        cols_no_sent = [c for c in new_cols if c != "sentiment"]
        run_ols_and_save(results_dir, df.copy(), cols_no_sent, ds_tag=f"{ds_tag}_no_sentiment")

        # ── Labelset evaluation metrics ────────────────────
        # 1) H_norm: normalized entropy over raw label scores
        eps = 1e-12
        S = df[candidate_labels].to_numpy(dtype=float)
        if S.size == 0 or len(candidate_labels) < 2:
            H_norm = np.nan
        else:
            ents = []
            for s_row in S:
                s_row = np.clip(s_row, 0.0, 1.0)
                den = s_row.sum()
                p = np.ones_like(s_row) / len(s_row) if den <= eps else s_row / den
                ents.append(float(-(p * np.log(p + eps)).sum()))
            mean_entropy = float(np.mean(ents)) if ents else np.nan
            H_norm = float(mean_entropy / np.log(len(candidate_labels))) if np.isfinite(mean_entropy) else np.nan

        # 2) Avg|corr|: mean absolute pairwise correlation among factor scores
        F = df[new_cols].copy()
        F = F.loc[:, [c for c in F.columns if F[c].nunique(dropna=True) > 1]]
        if F.shape[1] >= 2:
            C = F.corr().to_numpy()
            n = C.shape[0]
            avg_abs_corr = float(np.sum(np.abs(C - np.eye(n))) / (n * (n - 1)))
        else:
            avg_abs_corr = np.nan

        # 3) OOS R²: 5-fold cross-validation
        try:
            X_cv = df[new_cols].copy()
            X_cv = X_cv.loc[:, [c for c in X_cv.columns if X_cv[c].nunique() > 1]]
            y_cv = df["rating"].astype(float)
            if X_cv.shape[1] == 0 or len(X_cv) < 3:
                oos_r2 = np.nan
            else:
                k = min(5, max(2, len(df) // 5))
                kf = KFold(n_splits=k, shuffle=True, random_state=42)
                pred = np.zeros(len(y_cv), dtype=float)
                for tr, te in kf.split(X_cv):
                    pred[te] = LinearRegression().fit(X_cv.iloc[tr], y_cv.iloc[tr]).predict(X_cv.iloc[te])
                oos_r2 = float(r2_score(y_cv, pred))
        except Exception:
            oos_r2 = np.nan

        metrics_row = {
            "dataset":      ds_tag,
            "labelset":     cfg["name"],
            "suffix":       suffix,
            "H_norm":       H_norm,
            "avg_abs_corr": avg_abs_corr,
            "oos_r2":       oos_r2,
        }
        all_metrics.append(metrics_row)
        print(f"[METRICS] {metrics_row}")

    # ── Save all labelset metrics together (per dataset) ──
    metrics_path = os.path.join(base_results_dir, "labelset_eval_metrics.csv")
    pd.DataFrame(all_metrics).to_csv(metrics_path, index=False)
    print(f"\n[SAVED] {metrics_path}")

print("\n[DONE] All datasets completed.")