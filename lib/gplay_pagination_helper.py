"""Paginated Google Play review collection.

Utility for fetching more than one page of reviews per app (the base
`reviews()` call is capped at ~200 without a continuation token).
Not used by the default pipeline; kept for large-scale review collection.
"""

import time
from typing import List, Dict, Optional
from google_play_scraper import reviews as gp_reviews, Sort


def fetch_reviews_paginated(
    app_id: str,
    max_reviews: int = 1000,
    lang: str = "en",
    country: str = "us",
    sort: Sort = Sort.NEWEST,
    filter_score_with: Optional[int] = None,  # 1..5 to filter by star rating
    sleep_sec: float = 0.3,
) -> List[Dict]:
    """Fetch up to `max_reviews` reviews for one app, following continuation tokens."""
    all_reviews: List[Dict] = []
    batch, token = gp_reviews(
        app_id,
        lang=lang,
        country=country,
        sort=sort,
        count=min(200, max_reviews),
        filter_score_with=filter_score_with,
    )
    all_reviews.extend(batch)
    while token and len(all_reviews) < max_reviews:
        time.sleep(sleep_sec)
        batch, token = gp_reviews(app_id, continuation_token=token)
        all_reviews.extend(batch)
    return all_reviews[:max_reviews]


def collect_reviews_for_results(
    results: dict,
    lang: str = "en",
    country: str = "us",
    per_app_limit: int = 1000,
    sort: Sort = Sort.NEWEST,
    sleep_sec: float = 0.3,
    filter_score_with: Optional[int] = None,
) -> None:
    """Attach a `reviews` list to each Android app in `results` (in place)."""
    android_apps = results.get("android", [])
    for i, app in enumerate(android_apps, 1):
        app_id = app.get("appId")
        if not app_id:
            app["reviews"] = []
            continue
        try:
            print(f"[{i}/{len(android_apps)}] Fetching reviews: {app_id}")
            app["reviews"] = fetch_reviews_paginated(
                app_id,
                max_reviews=per_app_limit,
                lang=lang,
                country=country,
                sort=sort,
                filter_score_with=filter_score_with,
                sleep_sec=sleep_sec,
            )
            print(f"    -> collected {len(app['reviews'])} reviews")
        except Exception as e:
            print(f"[REVIEW ERROR] {app_id}: {e}")
            app["reviews"] = []
        time.sleep(sleep_sec)
