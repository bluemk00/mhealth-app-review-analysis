# Medical & Health App Review Analysis Pipeline

A reproducible pipeline that collects metadata and reviews of **medical / health / education apps**
from Google Play (and iOS), then runs preprocessing → sentiment/topic classification → regression analysis.

---

## 📂 Structure

```
.
├─ code/
│  ├─ settings.py                              # Config for 01 & 03 (collection volume, model, RUN_STAMP, labelsets)
│  ├─ 01_collect_android.py                    # App & review collection (script)
│  ├─ 02_preprocess.ipynb                      # Review cleaning + target-user classification
│  ├─ 03_sentiment_scoring_and_regression.py   # Zero-shot sentiment scoring + OLS regression
│  └─ 04_analysis_20250904.ipynb               # Main analysis / results (20250904)
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

| Step | File | Input → Output |
|------|------|----------------|
| 1 | `01_collect_android.py` | App store → `data/raw/..._<stamp>_android.json` (+ `_android_reviews.json`) |
| 2 | `02_preprocess.ipynb` | raw JSON → target-user classification + review cleaning / category split (**details below**) |
| 3 | `03_sentiment_scoring_and_regression.py` | `data/processed_<stamp>/cleaned_reviews_of_categoryN.csv` → `outputs/anal_res_<stamp>/categoryN/` |
| 4 | `04_analysis_20250904.ipynb` | Result aggregation, tables/figures |

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
├─ data/raw/                          # Anonymized JSON (content+score+at, no PII / gitignored)
├─ data/processed_20250904/           # Preprocessing outputs (gitignored) + app_target_users_validated.csv (committed)
└─ outputs/anal_res_20250904/         # Analysis results (gitignored)
```

### 🔒 Privacy & anonymization
**No reviewer personal data is stored** at collection/save time. The collector (`lib/collectors`, `01`)
reduces each record to only the fields needed for analysis before writing to disk (`slim_app_record`):
- **Review:** `content`, `score`, `at` — identifiers such as `userName`, `userImage`, `reviewId`, and replies are not stored.
- **App:** `appId`, `title`, `score`, `genre`, `free`, `installs`, `description`

So `data/raw/*_android.json` is **anonymized data** containing only what is needed for reproduction,
and it is committed to the repo. Because the same-date (20250904) snapshot cannot be re-collected,
this anonymized version is published for reproducibility (the pipeline ultimately uses only review
`content` + `score`).

### Data source & terms of use
- **Source:** Google Play (US, 2025-09-04 snapshot), collected with `google-play-scraper`.
- **Purpose:** Provided for **non-commercial academic reproducibility only.** Review text is copyright
  of the respective authors; app descriptions belong to the respective developers.
- **Privacy:** No reviewer-identifying information (name, profile, review ID, etc.) is included (anonymized).
- When redistributing or using commercially, comply with the Google Play Terms of Service and the rights
  of the original authors.

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
