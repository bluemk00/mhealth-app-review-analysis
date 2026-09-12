# Medical and health app review analysis

Code and data for our study of how consumer- and provider-targeted mobile health apps
differ in what drives review satisfaction (paper under review). The pipeline collects
Google Play reviews of medical, health, and education apps, labels each app by its
intended users (consumers/patients vs. healthcare providers), scores every review along
six quality dimensions with a zero-shot model, and fits the regressions reported in the
paper.

If you only want to reproduce the numbers in the paper, open
`code/provided/04_analysis_20250904.ipynb` and run it. Everything else below is context.

## Repository layout

```
code/
  settings.py                              shared config (run stamp, model, label sets)
  01_collect_android.py                    collect apps + reviews from Google Play
  02_preprocess.ipynb                      classify target users, clean and split reviews
  03_sentiment_scoring_and_regression.py   zero-shot factor scoring + OLS
  04_analysis_20250904.ipynb               tables and figures
  provided/                                the same pipeline, run from the released data only
lib/            scrapers and text-cleaning helpers used by steps 1-2
configs/        keyword lists and an empty API-key template
docs/           setup_guide.md
data/, outputs/ mostly git-ignored; see "Released data" below
```

## Reproducing the analysis

Steps 2-4 exist in two parallel copies. They read different inputs and write to different
places, so running one never disturbs the other.

**From the raw data — `code/01`-`04`.** The original pipeline, and the one that produced
the paper. Step 1 scrapes Google Play, step 2 calls the OpenAI API to draft the
target-user labels (and needs the raw collection JSON), step 3 scores the original review
text (a GPU helps). End to end it reproduces the paper exactly, but it needs the raw JSON,
which we don't distribute (see below) — so in practice only we can run it as is.

| Step | File | In → out |
|------|------|----------|
| 1 | `01_collect_android.py` | Google Play → `data/raw/..._android.json` |
| 2 | `02_preprocess.ipynb` | raw JSON → target-user labels + cleaned reviews per group |
| 3 | `03_sentiment_scoring_and_regression.py` | `cleaned_reviews_of_categoryN.csv` → `outputs/anal_res_<stamp>/` |
| 4 | `04_analysis_20250904.ipynb` | step-3 scores → tables and figures |

**From the released data — `code/provided/`.** These run on the de-identified files we
ship, with no raw JSON and no API key. The numbering follows the raw pipeline. Most people
only need step 4:

- `04_analysis_20250904.ipynb` reads `analysis_dataset.csv` and reproduces every table and
  figure in the paper — no GPU, no earlier steps. The factor scores are already in that
  file, so the output matches the paper exactly.
- `02_preprocess.ipynb` re-derives the selection funnel (1,022 apps → 388 eligible → 382
  classified → 325 analysed) from `app_selection_input_notext_20250904.json`, then writes
  the step-3 corpus. The selection filter only looks at review counts and dates, never at
  the review text, so the text-free input gives the same result.
- `03_sentiment_scoring_and_regression.py` (optional, GPU) re-runs the scoring on the
  masked corpus into `outputs/anal_res_<stamp>_provided/`. Since the input text is masked,
  the scores shift a little in the last digits — close to the paper but not bit-for-bit
  identical. It's here mainly to show the scoring step also runs on the released data.
- `01_make_notext_input.py` is how we produced the text-free JSON from the raw collection.
  It needs the raw JSON, so it isn't something a downstream user runs.

`code/provided/README.md` has the per-file input/output details.

### The target-user labels (step 2)

Step 2 labels each app consumer-, provider-, or other-targeted. We draft the labels by
prompting GPT with each app's store description, then the authors review all of them and
two of us reconcile a random sample by consensus. The reconciled labels live in
`data/processed_20250904/app_target_users_validated.csv` — the only label file in the
repo, and the one the rest of the pipeline reads. The GPT draft isn't deterministic, so
re-running that part won't match the validated labels exactly; the paper uses the
validated file.

## Released data, and why not the raw reviews

We don't ship the raw Google Play JSON. It holds the full text of every review, which can
contain things people wrote about themselves — a name, a phone number — and we can't
guarantee that's been scrubbed at the level of every single row; and redistributing
scraped reviews runs into both the Google Play terms and the reviewers' own copyright.
(The raw file is also what the selection code reads, since it uses per-review timestamps
and counts that never make it into the analysis table.)

What we release instead, under `data/processed_20250904/`:

| File | What it is |
|------|------------|
| `analysis_dataset.csv` | The 25,014 analysed reviews: group (HSC/HSP), rating, review text, six factor scores, sentiment. The text was read through by hand and any personal information replaced with tokens like `[NAME]` or `[PHONE]`. No app id, date, or install count. |
| `app_selection_table.csv` | One row per collected app — title, group, review count, latest review date, installs, free flag, and whether it passed the inclusion filter. App metadata only; no review text. |
| `app_selection_input_notext_20250904.json` | The collected app data with the review bodies stripped (each review keeps only its score and timestamp). This is what lets `provided/02` re-run the selection code rather than just trust the table above. |
| `app_target_users_validated.csv` | The validated consumer/provider labels. |

For the masking, we redacted personal information about private individuals and left
public figures, brand and product names, and app-featured creators as they were.
`app_selection_table.csv` and the text-free JSON contain no review text at all.

The rest of `data/` and `outputs/` is git-ignored. If you're setting up locally, the
layout the scripts expect is:

```
data/raw/                            raw JSON — local only, not committed
data/processed_20250904/             the four files above (committed) + git-ignored intermediates
outputs/anal_res_20250904/           author-track results (git-ignored)
outputs/anal_res_20250904_provided/  provided-track results (git-ignored)
```

The scraper already drops the obvious identifiers at collection time: it keeps only
`content`, `score`, and `at` for each review and a few app fields (`appId`, `title`,
`score`, `genre`, `free`, `installs`, `description`), and never stores user names, profile
images, review ids, or developer replies. The study was determined exempt by the Asan
Medical Center IRB (No. 2026-0856) as not involving identifiable individual-level data.

## Environment

Target: Python 3.13, Windows x64, and CUDA 12.8+ for the GPU steps. Install torch first
from the CUDA index, then the rest:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

Put the virtualenv somewhere outside a synced folder like Dropbox or OneDrive
(e.g. `C:\Users\<you>\venvs\medapp`) — `docs/setup_guide.md` explains why and lists the
verification steps. `requirements.lock.txt` has the exact versions we used.

The paper's numbers came from the environment in the Methods (scoring on Python 3.10 /
Transformers 4.55 / PyTorch 2.5.1+cu121, everything else on Python 3.8); this repo ships a
newer, consolidated one. Zero-shot scores move slightly across GPUs and library versions,
so re-running step 3 elsewhere can give marginally different factor scores. Step 4 is
deterministic once the scores are fixed, and the between-group findings hold either way.

Step 2 needs an OpenAI key. Keep it out of the repo: copy `configs/config_local.json` (an
empty template) to the folder just above the repository as `config_local.json` and fill it
in —

```json
{ "openai_api_key": "sk-...", "gpt_model": "gpt-5-2025-08-07" }
```

`02_preprocess.ipynb` runs from `code/` and reads `../../config_local.json`.

## License and reuse

The source code (`code/`, `lib/`, `configs/`) is MIT-licensed — see [`LICENSE`](LICENSE).
The validated label file, `app_target_users_validated.csv`, is our own work and is released
under CC BY 4.0.

The Google Play-derived data we release (`analysis_dataset.csv`, `app_selection_table.csv`,
and the text-free JSON) is third-party content and is *not* covered by the MIT license:
copyright in each review stays with its author, and the app metadata with the developers.
We share it only so others can reproduce the analyses non-commercially, and it remains
subject to the Google Play terms. Collected with `google-play-scraper` from the US Google
Play store, snapshot 2025-09-04.
