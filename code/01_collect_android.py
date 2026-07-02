"""Collect medical / health-education apps and their reviews from Google Play.

Run from anywhere:
    python code/01_collect_android.py

Outputs (the data/ folder is gitignored):
    data/raw/medical_health_education_apps_<YYYYMMDD>_android.json
    data/raw/medical_health_education_apps_<YYYYMMDD>_android_reviews.json
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Make the project root importable so `from lib...` works regardless of cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from lib.collectors.medical_app_collector import MedicalAppCollector

# Collection settings live in code/settings.py
from settings import (
    COUNTRY,
    LANGUAGE,
    TARGET_APP_COUNT,
    REVIEWS_PER_APP,
    REVIEW_SLEEP_SEC,
)


def main() -> None:
    collector = MedicalAppCollector(country=COUNTRY, language=LANGUAGE)

    # 1) Collect app metadata
    results = collector.collect_apps(platform="android", target_count=TARGET_APP_COUNT)
    print(f"Apps collected: {len(results['android'])}")

    # 2) Collect reviews per app
    for app in results["android"]:
        app_id = app.get("appId")
        if not app_id:
            continue
        review_list, _ = collector.android_scraper.reviews(app_id, count=REVIEWS_PER_APP)
        app["reviews"] = review_list
        time.sleep(REVIEW_SLEEP_SEC)
    total_reviews = sum(len(app.get("reviews", [])) for app in results["android"])
    print(f"Reviews collected: {total_reviews}")

    # 3) Save (writes *_android.json and *_android_reviews.json)
    date_stamp = datetime.now().strftime("%Y%m%d")
    base = PROJECT_ROOT / "data" / "raw" / f"medical_health_education_apps_{date_stamp}"
    collector.save_results(results, base_filename=str(base))
    print(f"Saved: {base}")


if __name__ == "__main__":
    main()
