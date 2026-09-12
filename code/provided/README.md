# Provided track

The same analysis as the top-level `code/`, but run entirely from the de-identified files
we release — no raw Google Play JSON, no OpenAI key. The step numbers mirror the author
track; paths here are relative to this folder, so the notebooks read `../../data/...`.

If you cloned the repo to check the paper, you really only need step 4.

**`04_analysis_20250904.ipynb`** reads `analysis_dataset.csv`, splits it by group, and
produces the tables and figures. The factor scores are already in that file, so this
reproduces the paper's numbers exactly, and it doesn't need a GPU. Verified against the
paper: n = 18,929 consumer / 6,085 provider, technical-stability β = 0.1989, the
provider-minus-consumer interaction = 0.0476.

**`02_preprocess.ipynb`** re-creates the app-selection funnel. It runs the same inclusion
filter (≥ 50 reviews, latest review on or after 2025-06-01, free, 1k-10M installs) on
`app_selection_input_notext_20250904.json` — the collected app data with the review bodies
removed. Selection only counts reviews and reads their timestamps, so the text-free input
gives the same funnel (1,022 → 388 → 382 → 325). It then splits the masked
`analysis_dataset.csv` into `cleaned_reviews_of_categoryN_provided.csv`, the input for step
3. No API, no GPU.

**`03_sentiment_scoring_and_regression.py`** is optional and wants a GPU. It re-scores the
masked corpus (reusing the author-track scorer) into `../../outputs/anal_res_20250904_provided/`.
The masking shifts the zero-shot scores a little in the last digits, so results here are
close to the paper but not identical to it. Run it only if you want to see the scoring step
work on the released text; step 4 already gives the exact numbers without it.

**`01_make_notext_input.py`** is how we built the text-free JSON above, by stripping each
review's body out of the raw collection. It needs the raw JSON, which isn't part of the
release, so it's for our use rather than a downstream reader's — the output it produces is
already committed.

## Running it

Set the environment up first (see the top-level README) and use that interpreter.

Reproduce the paper (step 4, no GPU) — open `04_analysis_20250904.ipynb` in Jupyter or VS
Code and run all cells. Headless, from this folder:

```bash
cd code/provided
jupyter nbconvert --to notebook --execute --inplace 04_analysis_20250904.ipynb
```

Re-derive the selection funnel (step 2) is the same with `02_preprocess.ipynb`. It also
writes the step-3 corpus, so run it before step 3.

```bash
cd code/provided
jupyter nbconvert --to notebook --execute --inplace 02_preprocess.ipynb
```

Re-score the masked corpus (step 3, optional, needs a GPU) — run step 2 first, then from
the repository root:

```bash
python code/provided/03_sentiment_scoring_and_regression.py
```

Rebuild the text-free input (step 1) only applies if you have the raw JSON:

```bash
python code/provided/01_make_notext_input.py
```
