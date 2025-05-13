import json
import os
from datetime import datetime

# Позволяем переопределить путь к кешу через переменную окружения
CACHE_PATH = os.getenv("FIAS_CACHE_PATH") or os.path.join(os.path.dirname(__file__), ".cache", "fias_cache.json")

os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, encoding="utf-8") as f:
        data = json.load(f)
        fias_cache = data.get("cache", {})
        cache_date = data.get("date")
else:
    fias_cache = {}
    cache_date = None


def is_stale():
    return cache_date != datetime.now().strftime("%Y-%m-%d")


def save_cache():
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "cache": fias_cache
        }, f, ensure_ascii=False, indent=2)
