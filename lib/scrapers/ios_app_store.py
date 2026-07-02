import requests
from typing import List, Dict, Optional, Tuple

from .base import AppStoreScraper


class iOSAppStoreScraper(AppStoreScraper):
    """iOS App Store scraper (uses the public iTunes Search/Lookup API)."""

    def __init__(self, country: str = 'us', language: str = 'en'):
        super().__init__(country, language)
        self.base_search_url = "https://itunes.apple.com/search"
        self.base_lookup_url = "https://itunes.apple.com/lookup"

    def search(self, keyword: str, n_hits: int = 50) -> List[Dict]:
        params = {
            'term': keyword,
            'country': self.country,
            'media': 'software',
            'limit': n_hits,
            'entity': 'software',
        }
        try:
            response = requests.get(self.base_search_url, params=params)
            response.raise_for_status()
            results = response.json().get('results', [])
            # Normalize to the Google Play field layout
            return [self._convert_app_data(app) for app in results]
        except Exception as e:
            print(f"Error searching iOS App Store for '{keyword}': {e}")
            return []

    def app(self, app_id: str) -> Dict:
        params = {'id': app_id, 'country': self.country}
        try:
            response = requests.get(self.base_lookup_url, params=params)
            response.raise_for_status()
            results = response.json().get('results', [])
            return self._convert_app_data(results[0], detailed=True) if results else {}
        except Exception as e:
            print(f"Error getting iOS app details for {app_id}: {e}")
            return {}

    def reviews(self, app_id: str, count: int = 100) -> Tuple[List[Dict], Optional[str]]:
        # The iTunes API does not expose reviews directly (an RSS feed would be needed).
        print(f"iOS review scraping is not implemented for {app_id} (requires RSS feed).")
        return ([], None)

    def _convert_app_data(self, app_data: Dict, detailed: bool = False) -> Dict:
        """Map an iTunes API record to the Google Play field layout."""
        converted = {
            'appId': str(app_data.get('trackId', '')),
            'title': app_data.get('trackName', ''),
            'developer': app_data.get('artistName', ''),
            'score': app_data.get('averageUserRating', 0) or 0,
            'genre': app_data.get('primaryGenreName', ''),
            'free': app_data.get('price', 0) == 0,
            'price': app_data.get('price', 0),
            'currency': app_data.get('currency', 'USD'),
            'summary': app_data.get('description', ''),
            'icon': app_data.get('artworkUrl512', app_data.get('artworkUrl100', '')),
            'ratings': app_data.get('userRatingCount', 0),
            'url': app_data.get('trackViewUrl', ''),
            'platform': 'ios',
            'version': app_data.get('version', ''),
            'releaseDate': app_data.get('releaseDate', ''),
            'bundleId': app_data.get('bundleId', ''),
            'sellerName': app_data.get('sellerName', ''),
            'contentRating': app_data.get('contentAdvisoryRating', ''),
            'screenshots': app_data.get('screenshotUrls', []),
            'supportedDevices': app_data.get('supportedDevices', []),
            'languageCodesISO2A': app_data.get('languageCodesISO2A', []),
            'fileSizeBytes': app_data.get('fileSizeBytes', 0),
            'minimumOsVersion': app_data.get('minimumOsVersion', ''),
            'trackContentRating': app_data.get('trackContentRating', ''),
            'genres': app_data.get('genres', []),
            'genreIds': app_data.get('genreIds', []),
        }
        if detailed:
            converted.update({
                'releaseNotes': app_data.get('releaseNotes', ''),
                'advisories': app_data.get('advisories', []),
                'isGameCenterEnabled': app_data.get('isGameCenterEnabled', False),
                'features': app_data.get('features', []),
                'currentVersionReleaseDate': app_data.get('currentVersionReleaseDate', ''),
                'formattedPrice': app_data.get('formattedPrice', ''),
            })
        return converted
