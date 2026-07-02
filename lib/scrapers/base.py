from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple


class AppStoreScraper(ABC):
    """Abstract base class for app store scrapers."""

    def __init__(self, country: str = 'us', language: str = 'en'):
        self.country = country
        self.language = language

    @abstractmethod
    def search(self, keyword: str, n_hits: int = 50) -> List[Dict]:
        """Search apps by keyword."""

    @abstractmethod
    def app(self, app_id: str) -> Dict:
        """Fetch app details."""

    @abstractmethod
    def reviews(self, app_id: str, count: int = 100) -> Tuple[List[Dict], Optional[str]]:
        """Fetch app reviews."""
