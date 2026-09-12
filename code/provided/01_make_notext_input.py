"""01 (PROVIDED track) - Build the review-text-free app input.

Author-only preparation step: derives the published, review-text-free app JSON
from the raw Google Play collection. Public users do NOT run this -- they use the
already-published output (`app_selection_input_notext_20250904.json`). It parallels
the author track's `01_collect_android.py`: both produce an input that downstream
steps consume, and both require data a public user does not have (raw JSON here,
the live Play Store there).

What it does
------------
For every app in the raw JSON it keeps ALL app-level fields (appId, title, score,
genre, free, installs, description) unchanged, and rewrites each review object from
``{content, score, at}`` to ``{score, at}`` -- i.e. it strips the review body
(``content``) while preserving the per-review timestamp/score that the selection
filter needs. No review free-text (and therefore no review-level PII) survives.

    raw:  {"appId": ..., "reviews": [{"content": "...", "score": 5, "at": "..."}]}
    out:  {"appId": ..., "reviews": [{"score": 5, "at": "..."}]}

Input  : ../../data/raw/medical_health_education_apps_<STAMP>_android.json   (local only)
Output : ../../data/processed_<STAMP>/app_selection_input_notext_<STAMP>.json (published)

Run from anywhere:
    python code/provided/01_make_notext_input.py
"""
import json
import os

STAMP = "20250904"

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))  # repository root
RAW = os.path.join(_ROOT, "data", "raw", f"medical_health_education_apps_{STAMP}_android.json")
OUT = os.path.join(_ROOT, "data", "processed_" + STAMP, f"app_selection_input_notext_{STAMP}.json")

KEEP_REVIEW_FIELDS = ("score", "at")  # everything except the review body ("content")


def main() -> None:
    with open(RAW, encoding="utf-8") as f:
        apps = json.load(f)

    detexted = []
    for app in apps:
        rec = dict(app)  # keep all app-level fields (incl. description)
        rec["reviews"] = [
            {k: r.get(k) for k in KEEP_REVIEW_FIELDS}
            for r in (app.get("reviews") or [])
            if isinstance(r, dict)
        ]
        detexted.append(rec)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(detexted, f, ensure_ascii=False)

    # Sanity: no review body must remain anywhere.
    leaked = any("content" in r for app in detexted for r in app["reviews"])
    n_reviews = sum(len(app["reviews"]) for app in detexted)
    print(f"apps: {len(detexted)} | reviews (metadata only): {n_reviews:,} | 'content' leaked: {leaked}")
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()
