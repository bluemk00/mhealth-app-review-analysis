from __future__ import annotations

import time
import json
import re
from pathlib import Path
from typing import List, Dict, Optional

from lib.scrapers.base import AppStoreScraper
from lib.scrapers.google_play import GooglePlayScraper
from lib.scrapers.ios_app_store import iOSAppStoreScraper


# Fields retained when persisting collected data. Everything else — in particular
# reviewer identity (userName, userImage, reviewId, replyContent, ...) — is dropped
# so that no personal data is ever written to disk. The analysis pipeline (02+)
# consumes only these fields.
APP_STORE_FIELDS = ("appId", "title", "score", "genre", "free", "installs", "description")
REVIEW_STORE_FIELDS = ("content", "score", "at")


def slim_app_record(app: Dict) -> Dict:
    """Return a copy of an app record with only analysis-necessary fields.

    App-level metadata is restricted to APP_STORE_FIELDS; each nested review is
    reduced to REVIEW_STORE_FIELDS (no reviewer name/image/id). Applied before
    writing to disk, so collected files never contain personal data.
    """
    out = {k: app.get(k) for k in APP_STORE_FIELDS}
    slim_reviews = []
    for r in app.get("reviews", []) or []:
        if isinstance(r, dict):
            slim_reviews.append({k: r.get(k) for k in REVIEW_STORE_FIELDS})
        elif isinstance(r, str):
            slim_reviews.append({"content": r, "score": None, "at": None})
    out["reviews"] = slim_reviews
    return out


class MedicalAppCollector:
    """Collect medical / health-education apps using the term lists in configs/."""

    def __init__(
        self,
        country: str = 'us',
        language: str = 'en',
        configs_dir: Optional[Path | str] = None,
    ):
        self.android_scraper = GooglePlayScraper(country, language)
        self.ios_scraper = iOSAppStoreScraper(country, language)

        # Default configs dir: <project_root>/configs (this file: lib/collectors/...)
        if configs_dir is None:
            configs_dir = Path(__file__).resolve().parents[2] / "configs"
        self.configs_dir = Path(configs_dir)

        self.medical_health_keywords = self._load_terms(self.configs_dir / "keywords_medical.txt")
        self.medical_terms = self._load_terms(self.configs_dir / "terms_medical.txt")
        self.pet_terms = self._load_terms(self.configs_dir / "terms_pet.txt")

        self.medical_terms_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(t) for t in self.medical_terms) + r')\b', re.IGNORECASE
        )
        self.pet_terms_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(t) for t in self.pet_terms) + r')\b', re.IGNORECASE
        )

    # ----- Public API -----
    def collect_apps(self, platform: str = 'both', target_count: int = 600) -> Dict[str, List[Dict]]:
        """Collect app metadata for the given platform(s).

        Reviews are not fetched here; collect them separately via
        scraper.reviews() (see 01_collect_android.ipynb).
        """
        results: Dict[str, List[Dict]] = {'android': [], 'ios': []}
        if platform.lower() in ('both', 'android'):
            print("=== Collecting Android apps ===")
            results['android'] = self._collect_platform_apps(self.android_scraper, 'Android', target_count)
        if platform.lower() in ('both', 'ios'):
            print("=== Collecting iOS apps ===")
            results['ios'] = self._collect_platform_apps(self.ios_scraper, 'iOS', target_count)
        return results

    def save_results(self, results: Dict[str, List[Dict]],
                     base_filename: str = 'medical_health_education_apps',
                     save_merged: bool = False):
        """Save collected apps (and a flattened review table) as JSON.

        `merged_data` is always returned, but only written to disk when
        `save_merged=True` (the analysis pipeline does not use the merged file).

        Records are slimmed to non-identifying fields (see slim_app_record)
        before writing, so no personal data is persisted.
        """
        results = {
            'android': [slim_app_record(a) for a in results.get('android', [])],
            'ios':     [slim_app_record(a) for a in results.get('ios', [])],
        }

        # Android apps
        if results['android']:
            android_filename = f"{base_filename}_android.json"
            Path(android_filename).parent.mkdir(parents=True, exist_ok=True)
            with open(android_filename, 'w', encoding='utf-8') as f:
                json.dump(results['android'], f, indent=2, ensure_ascii=False, default=str)
            print(f"Saved Android apps: {android_filename} ({len(results['android'])})")

            # Flattened reviews: one record per review
            android_reviews = []
            for app in results['android']:
                app_id = app.get('appId', 'unknown')
                title = app.get('title', 'unknown')
                for r in app.get('reviews', []):
                    if isinstance(r, dict):
                        android_reviews.append({'appId': app_id, 'title': title,
                                                'score': r.get('score'), 'text': r.get('content')})
                    elif isinstance(r, str):
                        android_reviews.append({'appId': app_id, 'title': title,
                                                'score': None, 'text': r})
            reviews_filename = f"{base_filename}_android_reviews.json"
            with open(reviews_filename, 'w', encoding='utf-8') as f:
                json.dump(android_reviews, f, indent=2, ensure_ascii=False)
            print(f"Saved Android reviews: {reviews_filename} ({len(android_reviews)})")

        # iOS apps
        if results['ios']:
            ios_filename = f"{base_filename}_ios.json"
            Path(ios_filename).parent.mkdir(parents=True, exist_ok=True)
            with open(ios_filename, 'w', encoding='utf-8') as f:
                json.dump(results['ios'], f, indent=2, ensure_ascii=False, default=str)
            print(f"Saved iOS apps: {ios_filename} ({len(results['ios'])})")

        # Merged view: not used by the pipeline; written only if requested.
        merged_data = self._merge_platform_data(results)
        if save_merged:
            merged_filename = f"{base_filename}_merged.json"
            with open(merged_filename, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Saved merged data: {merged_filename}")

        return merged_data

    def print_preview(self, results: Dict[str, List[Dict]], count: int = 30):
        """Print a short preview of collected apps and a summary."""
        for platform, apps in results.items():
            if apps:
                print(f"\n=== {platform.upper()} top {min(count, len(apps))} apps ===")
                for i, app in enumerate(apps[:count], 1):
                    score = app.get('score') or 0
                    title = app.get('title', 'Unknown')
                    app_id = app.get('appId', 'Unknown')
                    price = "Free" if app.get('free', True) else f"${app.get('price', 0)}"
                    print(f"{i:2d}. {title} - {app_id} (Score: {score:.2f}, {price})")

        total_apps = len(results['android']) + len(results['ios'])
        print(f"\n=== Summary ===")
        print(f"Android apps: {len(results['android'])}")
        print(f"iOS apps: {len(results['ios'])}")
        print(f"Total: {total_apps}")

    # ----- Internal helpers -----
    def _collect_platform_apps(self, scraper: AppStoreScraper, platform_name: str,
                               target_count: int) -> List[Dict]:
        """Search each keyword, filter to medical/health apps, dedup, and sort by score."""
        all_apps: List[Dict] = []
        total_found = 0

        print(f"Starting {platform_name} search with {len(self.medical_health_keywords)} keywords...")
        for i, keyword in enumerate(self.medical_health_keywords, 1):
            try:
                print(f"[{i}/{len(self.medical_health_keywords)}] Searching: '{keyword}'")
                found = self._filter_medical_apps(scraper.search(keyword, n_hits=50))
                all_apps.extend(found)
                total_found += len(found)
                print(f"  Found {len(found)} medical/health apps (Total: {total_found})")
                time.sleep(0.4)  # rate limit
                if total_found >= target_count:
                    print(f"Target reached! Found {total_found} apps.")
                    break
            except Exception as e:
                print(f"  Error searching for '{keyword}': {e}")
                time.sleep(1)

        # Dedup by appId, then sort by score (desc)
        unique_apps = list({app['appId']: app for app in all_apps if app.get('appId')}.values())
        print(f"Before dedup: {len(all_apps)} / After dedup: {len(unique_apps)}")
        return sorted(unique_apps, key=lambda x: (x.get('score') or 0), reverse=True)

    def _filter_medical_apps(self, apps: List[Dict]) -> List[Dict]:
        """Keep apps whose title/summary match a medical term but no pet term."""
        out: List[Dict] = []
        for app in apps:
            text = f"{app.get('title', '') or ''} {app.get('summary', '') or ''}"
            if self.medical_terms_pattern.search(text) and not self.pet_terms_pattern.search(text):
                out.append(app)
        return out

    def _merge_platform_data(self, results: Dict[str, List[Dict]]) -> Dict:
        """Combine Android/iOS results with basic statistics."""
        return {
            'android_apps': results['android'],
            'ios_apps': results['ios'],
            'total_android': len(results['android']),
            'total_ios': len(results['ios']),
            'combined_total': len(results['android']) + len(results['ios']),
            'statistics': {
                'android': self._calculate_platform_stats(results['android'], 'Android'),
                'ios': self._calculate_platform_stats(results['ios'], 'iOS'),
            },
        }

    def _calculate_platform_stats(self, apps: List[Dict], platform_name: str) -> Dict:
        """Compute per-platform summary statistics."""
        if not apps:
            return {'platform': platform_name, 'total_apps': 0}

        numeric_scores = [s for s in (app.get('score') for app in apps) if isinstance(s, (int, float))]
        stats = {
            'platform': platform_name,
            'total_apps': len(apps),
            'avg_rating': (sum(numeric_scores) / len(numeric_scores)) if numeric_scores else 0,
            'free_apps': sum(1 for app in apps if app.get('free', True)),
            'paid_apps': sum(1 for app in apps if not app.get('free', True)),
        }
        categories: Dict[str, int] = {}
        for app in apps:
            cat = app.get('genre', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        stats['categories'] = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
        return stats

    # ----- Config loader -----
    def _load_terms(self, filepath: Path | str) -> List[str]:
        """Load non-empty, stripped lines from a config file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
