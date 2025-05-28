import json
import os


def load_existing_mappings(filepath):
    """Загружает JSON-выгрузку справочника из файла."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    return [
        {
            "source": {"fias_id": row["clientCityId"]},
            "target": {"fias_id": row["targetCityId"]}
        }
        for row in data
    ]


def load_json_or_empty(path):
    if not os.path.exists(path):
        print(f"⚠️ Файл исключений не найден: {path}")
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Ошибка при чтении {path}: {e}")
        return {}
