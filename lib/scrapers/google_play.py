from typing import List, Dict, Optional, Tuple

from google_play_scraper import search as gp_search
from google_play_scraper import reviews as gp_reviews
from google_play_scraper import app as gp_app

from .base import AppStoreScraper


class GooglePlayScraper(AppStoreScraper):
    """Google Play Store scraper (wraps the google-play-scraper package)."""

    def search(self, keyword: str, n_hits: int = 50) -> List[Dict]:
        try:
            results = gp_search(keyword, lang=self.language, country=self.country, n_hits=n_hits)
            for app in results:
                app['platform'] = 'android'
            return results
        except Exception as e:
            print(f"Error searching Google Play for '{keyword}': {e}")
            return []

    def app(self, app_id: str) -> Dict:
        try:
            app_info = gp_app(app_id, lang=self.language, country=self.country)
            app_info['platform'] = 'android'
            return app_info
        except Exception as e:
            print(f"Error getting Google Play app details for {app_id}: {e}")
            return {}

    def reviews(self, app_id: str, count: int = 100) -> Tuple[List[Dict], Optional[str]]:
        try:
            return gp_reviews(app_id, lang=self.language, country=self.country, count=count)
        except Exception as e:
            print(f"Error getting Google Play reviews for {app_id}: {e}")
            return ([], None)
