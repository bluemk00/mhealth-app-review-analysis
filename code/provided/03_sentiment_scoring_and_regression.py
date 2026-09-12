"""03 (PROVIDED track) - Sentiment scoring & regression on the de-identified corpus.

Reuses the author-track scorer verbatim (``code/03_sentiment_scoring_and_regression.py``)
but wires it to the provided-track data:

  * INPUT  : ../../data/processed_<STAMP>/cleaned_reviews_of_categoryN_provided.csv
             (written by provided/02_preprocess.ipynb; PII-masked review text)
  * OUTPUT : ../../outputs/anal_res_<STAMP>_provided/  (kept separate from the author track)

Because the input text is PII-masked ([NAME], [EMAIL], ...), zero-shot scores drift at
the low-order digits, so results are ~identical (NOT byte-identical) to the paper. For
byte-exact paper numbers use ``provided/04_analysis_20250904.ipynb`` (reads the scores
already embedded in ``analysis_dataset.csv``; no GPU).

Run from anywhere (requires the same environment as the author 03: torch + transformers):
    python code/provided/03_sentiment_scoring_and_regression.py
"""
import os
import sys
import runpy

# The author-track scorer uses paths relative to code/ (e.g. ../data, ../outputs) and
# imports settings. Switch into code/ so those resolve, and expose it on sys.path.
_HERE = os.path.dirname(os.path.abspath(__file__))     # code/provided
_CODE = os.path.dirname(_HERE)                          # code
os.chdir(_CODE)
sys.path.insert(0, _CODE)

from settings import RUN_STAMP  # noqa: E402

# Provided-track inputs (masked corpus) and a separate provided-track output tree.
os.environ["INPUT_CSV_CAT1"] = f"../data/processed_{RUN_STAMP}/cleaned_reviews_of_category1_provided.csv"
os.environ["INPUT_CSV_CAT2"] = f"../data/processed_{RUN_STAMP}/cleaned_reviews_of_category2_provided.csv"
os.environ["RESULTS_DIR_CAT1"] = f"../outputs/anal_res_{RUN_STAMP}_provided/category1/"
os.environ["RESULTS_DIR_CAT2"] = f"../outputs/anal_res_{RUN_STAMP}_provided/category2/"

# The provided corpus was already filtered to >= 3 words on the ORIGINAL text before
# masking (that is exactly the 25,014-review analysis_dataset.csv). Masking only shortens
# text, so re-applying the 3-word cut here would wrongly drop masked-short reviews. Set the
# threshold to 1 (drop only empty rows) so the full 25,014-review corpus is scored.
os.environ["MIN_REVIEW_WORDS"] = "1"

print(
    "[PROVIDED track] scoring the PII-masked corpus -> "
    f"../outputs/anal_res_{RUN_STAMP}_provided/  (results ~identical to the paper)"
)

# Reuse the exact scoring + regression pipeline from the author-track script.
runpy.run_path("03_sentiment_scoring_and_regression.py", run_name="__main__")
