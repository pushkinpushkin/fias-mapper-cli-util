import json
import os
from datetime import datetime


class FiasCache:
    def __init__(self, cache_path=None):
        # Позволяем переопределить путь к кешу через переменную окружения
        default_path = os.path.join(os.path.dirname(__file__), ".cache", "fias_cache.json")
        self.cache_path = cache_path or os.getenv("FIAS_CACHE_PATH") or default_path
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        self.cache = {}
        self.cache_date = None
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)
                self.cache = data.get("cache", {})
                self.cache_date = data.get("date")

    def is_stale(self):
        return self.cache_date != datetime.now().strftime("%Y-%m-%d")

    def save(self):
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "cache": self.cache
            }, f, ensure_ascii=False, indent=2)
