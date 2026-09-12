# Provided track (`code/provided/`)

The study pipeline **run on the published, de-identified data only** — no raw Google Play
JSON and no OpenAI key. It mirrors the author track (`code/01–04`) step-for-step but reads
the de-identified files under `data/processed_20250904/`.

| # | File | Reads | Writes | Notes |
|---|------|-------|--------|-------|
| 01 | `01_make_notext_input.py` | `../../data/raw/…_android.json` (raw, **local only**) | `../../data/processed_20250904/app_selection_input_notext_20250904.json` | **Author-only.** Strips each review's body (`content`), keeping app metadata + per-review `{score, at}`. Public users skip this and use the published output. |
| 02 | `02_preprocess.ipynb` | `app_selection_input_notext_20250904.json`, `app_target_users_validated.csv`, `analysis_dataset.csv` | `app_selection_table.csv`, `cleaned_reviews_of_categoryN_provided.csv` | Reproduces the app-selection funnel (1,022 → 388 → 382 → 325) from the **text-free** JSON, then builds the Step-3 corpus by splitting the masked `analysis_dataset.csv`. No API, no GPU. |
| 03 | `03_sentiment_scoring_and_regression.py` | `cleaned_reviews_of_categoryN_provided.csv` | `../../outputs/anal_res_20250904_provided/` | **Optional; GPU.** Re-scores the **masked** corpus (reuses the author scorer). Results are **~identical** (not byte-identical) — masking shifts zero-shot scores slightly. |
| 04 | `04_analysis_20250904.ipynb` | `analysis_dataset.csv` | tables/figures | Reproduces every reported number **exactly**, **no GPU**, from the factor scores already embedded in `analysis_dataset.csv` (split by `group`). |

## How to reproduce the paper (public repo clone)

1. Open `04_analysis_20250904.ipynb` and run all → exact tables/figures. That's it; it needs
   only `analysis_dataset.csv`.
2. To also reproduce the **app-selection funnel**, run `02_preprocess.ipynb` (reads the
   text-free JSON). `01` and `03` are optional and are **not** needed for the paper's numbers.

## Numbering

Numbers match the author track by role: **01** produces the track's input (author-only, like
author `01_collect_android.py`), and **02–04** are the reproducible steps that mirror author
`02/03/04`. Paths are relative to this folder, so notebooks use `../../data/…`.

See the repository `README.md` → *Two tracks* for the full rationale and the exact-vs-similar
guarantee.
