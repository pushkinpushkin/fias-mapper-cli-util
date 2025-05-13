import json


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
