# Medical & Health App Review Analysis Pipeline

A reproducible pipeline that collects metadata and reviews of **medical / health / education apps**
from Google Play (and iOS), then runs preprocessing → sentiment/topic classification → regression analysis.

---

## 📂 Structure

```
.
├─ code/                                       # Author track — runs on RAW data (needs raw JSON + OpenAI key)
│  ├─ settings.py                              # Config for 01 & 03 (collection volume, model, RUN_STAMP, labelsets)
│  ├─ 01_collect_android.py                    # App & review collection (script)
│  ├─ 02_preprocess.ipynb                      # Review cleaning + target-user classification (raw JSON)
│  ├─ 03_sentiment_scoring_and_regression.py   # Zero-shot sentiment scoring + OLS regression
│  ├─ 04_analysis_20250904.ipynb               # Main analysis / results (reads Step-3 outputs)
│  └─ provided/                                # Provided track — runs on the de-identified data (no raw JSON / no API)
│     ├─ 01_make_notext_input.py               # (author-only) raw JSON → review-text-free app JSON
│     ├─ 02_preprocess.ipynb                   # Selection funnel (text-free JSON) + Step-3 corpus
│     ├─ 03_sentiment_scoring_and_regression.py# Optional re-scoring of masked corpus (GPU)
│     ├─ 04_analysis_20250904.ipynb            # Exact reproduction from analysis_dataset.csv (no GPU)
│     └─ README.md                             # Provided-track guide
├─ lib/                                        # Reusable package
│  ├─ collectors/   medical_app_collector.py
│  ├─ scrapers/     base.py · google_play.py · ios_app_store.py
│  └─ utils/        text_preprocessing.py
├─ configs/                                    # Keyword / filter term lists + key template
│  ├─ keywords_medical.txt · terms_medical.txt · terms_pet.txt
│  └─ config_local.json (empty template) · README.md
├─ docs/setup_guide.md                         # Environment setup guide
├─ requirements.txt · requirements.lock.txt
├─ .gitignore
└─ README.md
```

`data/` (except the validated label file) and `outputs/` are large and are **excluded from the
repository (.gitignore)**. See "Data layout" below.

---

## 🔁 Pipeline

The pipeline exists in **two fully separated tracks** (see *Two tracks* below for the rationale and the
exact-vs-similar guarantee):

**Author track** — original code, runs on the **raw** data; reproduces the paper *exactly*. Needs the local
raw JSON and an OpenAI key (Step 2).

| Step | File | Input → Output |
|------|------|----------------|
| 1 | `01_collect_android.py` | App store → `data/raw/..._<stamp>_android.json` (+ `_android_reviews.json`) |
| 2 | `02_preprocess.ipynb` | raw JSON → target-user classification + review cleaning / category split (**details below**) |
| 3 | `03_sentiment_scoring_and_regression.py` | `cleaned_reviews_of_categoryN.csv` → `outputs/anal_res_<stamp>/categoryN/` |
| 4 | `04_analysis_20250904.ipynb` | `outputs/anal_res_<stamp>/categoryN_2/scores_with_factors.csv` → tables/figures |

**Provided track** — lives in `code/provided/`, runs on the **published de-identified data only** (no raw
JSON, no API). Same numbering as the author track: `01` produces the track's input (author-only, like author
Step 1), `02–04` are the reproducible steps.

| Step | File (`code/provided/`) | Input → Output |
|------|------|----------------|
| 1 | `01_make_notext_input.py` | *(author-only)* raw JSON → `app_selection_input_notext_<stamp>.json` (review body removed) |
| 2 | `02_preprocess.ipynb` | `app_selection_input_notext_<stamp>.json` (+ `analysis_dataset.csv`) → selection funnel + `cleaned_reviews_of_categoryN_provided.csv` |
| 3 | `03_sentiment_scoring_and_regression.py` | `cleaned_reviews_of_categoryN_provided.csv` → `outputs/anal_res_<stamp>_provided/` — *optional; GPU; re-scores masked text (~identical results)* |
| 4 | `04_analysis_20250904.ipynb` | `analysis_dataset.csv` → tables/figures (**exact** paper numbers, no GPU) |

### Step 2 in detail — target-user (consumer/provider) classification
A two-stage **GPT auto-draft → human validation** process that automates what the authors originally did by hand.

1. **Auto draft** — `02` classifies each app's description with GPT and produces
   `data/processed_<stamp>/app_information_with_description.csv`
   (columns: app info + `Description` + `machine_key` + `Target_Users` + `gpt_reason`).
2. **Human validation** — the authors review every item, and two corresponding authors review a
   random sample and reach consensus, producing the final labels
   `data/processed_<stamp>/app_target_users_validated.csv` (`AppId`, `Title`, `Target_Users`).
   *(The only validated artifact committed to the repo, and the file `02` actually reads.)*
3. **Review split** — the later part of `02` splits reviews into category1/2 using the `Target_Users`
   values in `app_target_users_validated.csv`, saving `cleaned_reviews_of_categoryN.csv` etc.
   (→ input to Step 3).

> ⚠️ **The paper's numbers are reproduced from the validated `app_target_users_validated.csv`.**
> The GPT auto-draft is provided for reproducibility/transparency and may differ slightly from the
> validated assignments (GPT non-determinism + human review). Readers can auto-reproduce through
> step 1 even without the validated file.

### What is published, and why the raw review JSON is **not**
The published dataset is intentionally split into separate de-identified files (review-level and
app-level), and the raw per-review JSON is **not** redistributed. The reason is a hard constraint, not a
preference:

- The **app-inclusion filter** in Step 2 (see `02_preprocess.ipynb`, "Step 1: Filter apps") is computed
  from fields that live **only in the raw Google Play JSON** — per-review timestamps (`at`, used to derive
  each app's *latest review date*) and per-app **review counts**, together with `installs` / `free`. None of
  these survive into the analysis table, so the selection step cannot be reproduced from the review-level file
  alone.
- That same raw JSON also holds the **full free text of every collected review**, which can contain incidental
  personal information (self-disclosed names, contact details) that cannot be *exhaustively* guaranteed removed
  at the row level, and whose redistribution is additionally restricted by the **Google Play Terms of Service**
  and by copyright in each individual review.

Publishing the raw JSON would therefore either re-expose review-level free text or violate the ToS. To keep the
study reproducible **without** doing so, we publish:

| Published file | Contents | Enables |
|----------------|----------|---------|
| `data/processed_20250904/analysis_dataset.csv` | 25,014 analysis-ready reviews: `group` (HSC/HSP), `rating`, PII-**masked** `review`, six factor scores, `sentiment`. No `appId` / date / installs. | Exact reproduction of **all reported statistics** (Step 4). |
| `data/processed_20250904/app_selection_table.csv` | One row per collected app: `AppId`, `Title`, `group`, `Nb_Reviews`, `Latest_Review_Date`, `Nb_Installs`, `Free`, `eligible`. **Aggregate app metadata only — contains no review text.** | Verification / reproduction of the **app-selection step** (review-count ≥ 50, latest review ≥ 2025-06-01, free, installs 1k–10M). |
| `data/processed_20250904/app_selection_input_notext_20250904.json` | The collected app data (1,022 apps) with **review `content` removed** — each review keeps only `score` + `at`; app metadata (incl. `description`) is retained. **No review body text.** | Running the provided track's selection step (`02_preprocess_provided`) on real code, not just a precomputed table. |
| `data/processed_20250904/app_target_users_validated.csv` | `AppId`, `Title`, `Target_Users` (2-author consensus labels). | The validated consumer/provider assignment used downstream. |

**Selection funnel (reproducible from `app_selection_table.csv`).** Applying the Step-2 criteria to the
2025-09-04 snapshot: **1,022** collected apps → **388** meet the automated inclusion criteria (`eligible = True`)
→ **382** retained in the validated classification (`group` populated) → **325** classified as consumer (`HSC`,
234) or provider (`HSP`, 91); the remaining 57 are `other` and excluded from analysis. The 6-app gap between
*eligible* (388) and *validated* (382) are borderline cases at the thresholds (e.g., exactly 100 stored reviews
— the per-app fetch cap — or a latest-review date within days of the 2025-06-01 cutoff) that were not carried
into the validated set; the analyzed set (325 apps → 25,014 reviews) matches the paper.

> Note: `app_selection_table.csv` is generated from the raw JSON but deliberately excludes the `Description`
> field and all review text; it exists so the review-count/recency filters remain auditable after the raw JSON
> is withheld.

### Two tracks — author (raw) vs provided (de-identified)
The analysis is shipped as **two independent, non-overlapping sets of files**. They never share an input or
output path, so running one never disturbs the other.

**1. Author track** — `01_…`, `02_preprocess.ipynb`, `03_…py`, `04_analysis_20250904.ipynb` (no suffix).
Runs the study end-to-end from the **raw Google Play JSON**: live selection + GPT classification (Step 2, needs
an OpenAI key), zero-shot scoring on the original review text (Step 3, GPU), regression (Step 4). This is the
code that produced the paper and reproduces its numbers **exactly**. It requires the raw JSON, which is **not
redistributed** (kept local only; see below), so only the original authors can run this track as-is.

**2. Provided track** — the `code/provided/` folder (`01_make_notext_input.py`, `02_preprocess.ipynb`,
`03_sentiment_scoring_and_regression.py`, `04_analysis_20250904.ipynb`; see `code/provided/README.md`).
Numbering mirrors the author track; paths are relative to that folder (`../../data/…`). Runs on the
**published de-identified data only** — no raw JSON, no OpenAI key:

- **`01_make_notext_input.py`** *(author-only)* derives the published `app_selection_input_notext_20250904.json`
  from the raw JSON by removing each review's body (`content`) while keeping app metadata and per-review
  `{score, at}`. Like author Step 1 it needs data a public user does not have (the raw JSON), so a clone uses the
  already-published output and skips this file. Re-running it reproduces the JSON byte-for-byte.
- **`02_preprocess.ipynb`** reproduces the **app-selection funnel** by running the *identical* filter
  (review-count ≥ 50, latest review ≥ 2025-06-01, free, installs 1k–10M) on
  `app_selection_input_notext_20250904.json` — the collected app data with **all review text removed**
  (only per-review timestamps/scores + app metadata remain). App selection never reads review *bodies*, so this
  text-free input yields the **identical** selection (1,022 → 388 eligible → 382 validated → 325 analyzed). It
  then builds the Step-3 corpus (`cleaned_reviews_of_categoryN_provided.csv`) by splitting the PII-masked
  `analysis_dataset.csv` by group.
- **`03_sentiment_scoring_and_regression.py`** *(optional; GPU)* re-scores that masked corpus into
  `outputs/anal_res_20250904_provided/` (it reuses the author-track scorer). Because the text is masked
  (`[NAME]`, `[EMAIL]`, …), zero-shot scores drift at the low-order digits, so its results are **~identical, not
  byte-identical**, to the paper.
- **`04_analysis_20250904.ipynb`** reproduces every table/figure **exactly** and **without a GPU**, by reading
  the already-computed factor scores embedded in `analysis_dataset.csv` (split by `group`). Verified:
  n = 18,929 / 6,085, and identical OLS coefficients (e.g., technical-stability β = 0.1989, Provider–Consumer
  interaction = 0.0476).

> **Which should I run?** For the paper's exact numbers on a clone of the public repo, run
> `code/provided/04_analysis_20250904.ipynb` — it needs neither the raw data nor a GPU. Run
> `code/provided/03_…` only to demonstrate that the scoring step also executes on the de-identified corpus. The
> **author track** (`code/01–04`) is preserved verbatim for authors/re-collectors who have the raw JSON.

### run-stamp convention
- `03` builds paths from **`RUN_STAMP`** in `settings.py` (e.g., `20250904`).
  - Input:  `../data/processed_<stamp>/cleaned_reviews_of_categoryN.csv`
  - Output: `../outputs/anal_res_<stamp>/categoryN/`
- **Main dataset = `20250904`** (default). Other dates (e.g., 20260518) are experimental.
- All settings for `01` and `03` (collection volume, model, labelsets, ...) live in `code/settings.py`.

### Data layout
Since scripts run from `code/`, place data/outputs at the **repository root** as follows:
```
.
├─ data/raw/                          # Raw Google Play JSON — kept LOCAL ONLY, NOT redistributed (gitignored)
│                                     #   (holds review free-text + per-review `at`; see "why" above)
├─ data/processed_20250904/           # Intermediate outputs are gitignored; four de-identified files are PUBLISHED:
│                                     #     • analysis_dataset.csv                     (masked reviews — reproduces Step 4)
│                                     #     • app_selection_table.csv                  (app metadata only — Step-2 funnel, human-readable)
│                                     #     • app_selection_input_notext_20250904.json (text-free app JSON — runs 02_provided selection)
│                                     #     • app_target_users_validated.csv           (validated consumer/provider labels)
│                                     #   (cleaned_reviews_of_*_provided.csv are regenerated by 02_provided; gitignored)
├─ outputs/anal_res_20250904/          # Author-track analysis results (gitignored)
└─ outputs/anal_res_20250904_provided/ # Provided-track (03_provided) results (gitignored)
```

### 🔒 Privacy & anonymization
**No reviewer personal data is stored** at collection/save time. The collector (`lib/collectors`, `01`)
reduces each record to only the fields needed for analysis before writing to disk (`slim_app_record`):
- **Review:** `content`, `score`, `at` — identifiers such as `userName`, `userImage`, `reviewId`, and replies are not stored.
- **App:** `appId`, `title`, `score`, `genre`, `free`, `installs`, `description`

**Direct reviewer identifiers (user name, profile image, review ID) and developer replies are removed at
collection time** (see fields above). The raw `data/raw/*_android.json` — which still holds each review's
free text and timestamp — is **kept local and is not redistributed** (see "What is published, and why the raw
review JSON is not", above). What we publish instead is de-identified:

- **`analysis_dataset.csv`** carries the review free text, but every review was additionally passed through an
  **exhaustive cell-by-cell PII-masking review**: incidental personal information written into the free text
  (names, emails, phone numbers, addresses) is replaced with placeholder tokens (`[NAME]`, `[EMAIL]`,
  `[PHONE]`, `[ADDRESS]`). It contains no `appId`, no timestamp, and no other row-level metadata.
- **`app_selection_table.csv`** contains only aggregate app metadata (counts, dates, install buckets) and
  **no review text at all**.

Public figures, brand/app/product names, and app-featured creators are intentionally left unmasked; only the
personal information of private individuals is redacted.

### Data source & terms of use
- **Source:** Google Play (US, 2025-09-04 snapshot), collected with `google-play-scraper`.
- **Purpose:** Provided for **non-commercial academic reproducibility only.** Review text is copyright
  of the respective authors; app descriptions belong to the respective developers.
- **Privacy:** No direct reviewer identifiers (user name, profile image, review ID) are included; incidental
  self-disclosed names in the free text were redacted. This study was determined exempt by the Asan Medical
  Center IRB (No. 2026-0856) as not involving identifiable individual-level data.
- When redistributing or using commercially, comply with the Google Play Terms of Service and the rights
  of the original authors.

---

## 📄 License

This repository combines original source code with third-party data, licensed separately:

- **Source code** (`code/`, `lib/`, `configs/`) — MIT License; see [`LICENSE`](LICENSE).
- **Study-generated labels** (`data/processed_20250904/app_target_users_validated.csv`) — human-validated
  app-classification labels created by the authors; released under CC BY 4.0.
- **Google Play–derived data** — the published, de-identified `data/processed_20250904/analysis_dataset.csv`
  (PII-masked review text) and `data/processed_20250904/app_selection_table.csv` (aggregate app metadata) —
  **third-party content, NOT covered by the MIT License or any license granted by the authors.** Copyright in
  each review remains with its author, and app titles/metadata with the respective developers. The raw
  per-review JSON is not redistributed. This data is provided solely to enable non-commercial academic
  reproduction of this study's analyses, and remains subject to applicable copyright and the Google Play Terms
  of Service.

---

## 🔑 API key setup (for GPT classification in 02_preprocess)

The key is **not included in the repository.** Keep the real key file in the **parent folder of the repository.**

1. Copy `configs/config_local.json` (empty template) to the folder **directly above the repository**
   as `config_local.json`:
   ```
   <parent folder>/
   ├─ config_local.json   ← here (real key, gitignored, outside the repo)
   └─ <repo>/             ← repository root
      └─ code/
   ```
2. Enter the key in the file:
   ```json
   { "openai_api_key": "sk-...", "gpt_model": "gpt-5-2025-08-07" }
   ```
3. `02_preprocess.ipynb` runs from `code/` and reads the key from `../../config_local.json` (= the parent folder).

> Earlier versions had the key hard-coded in the notebook; it has been removed.
> `configs/config_local.json` is a template with an **empty** key.

---

## ⚙️ Environment

| File | Purpose |
|------|---------|
| `requirements.txt` | Dependency list for installation (excludes torch — mind the order below) |
| `requirements.lock.txt` | Full pinned versions of a verified install (reproducibility reference) |
| [`docs/setup_guide.md`](docs/setup_guide.md) | Detailed environment setup guide (Python, venv, CUDA, verification) |

**Install (summary)** — target: Python 3.13 / Windows x64 / (with GPU) CUDA 12.8+
```bash
# 1) Install torch FIRST from the CUDA 12.8 index (do NOT `pip install torch` — that grabs the CPU build)
pip install torch --index-url https://download.pytorch.org/whl/cu128
# 2) Everything else
pip install -r requirements.txt
```
> ⚠️ Create the virtual environment **outside Dropbox/OneDrive** (e.g., `C:\Users\<you>\venvs\medapp`).
> See [`docs/setup_guide.md`](docs/setup_guide.md) for the reasons and verification steps.

> **Reproducibility note.** The results reported in the paper were produced with the *original* analysis
> environment described in the paper's Methods (sentiment scoring: Python 3.10.18, Transformers 4.55.0,
> PyTorch 2.5.1 / CUDA 12.1; collection, app categorization, and statistics: Python 3.8.20). This repository
> ships an *updated, consolidated* environment (Python 3.13, PyTorch cu128). Zero-shot scores vary slightly
> at the low-order digits with GPU and library version, so re-running Step 3 on different hardware may yield
> marginally different factor scores; the downstream regression (Step 4) is deterministic given those scores,
> and the between-group findings are stable across environments.
