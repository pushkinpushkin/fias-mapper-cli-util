import os
import shutil
import pandas as pd
import json
from datetime import datetime


# Создание директории с меткой времени
def create_report_folder():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    folder_path = os.path.join("reports", timestamp)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


# Сохраняет Excel-отчёт в указанную папку
def save_excel_report(data, folder, name_postfix):
    df = pd.DataFrame([{
        "source_city": item["source"]["name"],
        "source_id": item["source"]["fias_id"],
        "target_city": item["target"]["name"],
        "target_id": item["target"]["fias_id"]
    } for item in data])
    excel_name = "report_" + name_postfix + ".xlsx"
    filename = os.path.join(folder, excel_name)
    df.to_excel(filename, index=False)
    print(f"📊 Excel-отчёт сохранён: {filename}")


# Сохраняет JSON-отчёт в указанную папку
def save_json_report(data, folder, name_postfix):
    json_name = "data_" + name_postfix + ".json"
    filename = os.path.join(folder, json_name)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📄 JSON-файл сохранён: {filename}")


def save_source_excel(source_excel_path, folder):
    if os.path.exists(source_excel_path):
        original_name = os.path.basename(source_excel_path)
        destination_path = os.path.join(folder, original_name)
        shutil.copy(source_excel_path, destination_path)
        print(f"📥 Исходный Excel скопирован: {original_name}")
    else:
        print(f"⚠️ Файл {source_excel_path} не найден, пропущен")


def save_current_dict_json(original_path, folder):
    """
    Копирует JSON-файл справочника в папку отчёта.
    """
    if os.path.exists(original_path):
        filename = os.path.join(folder, "current_dict.json")
        shutil.copy(original_path, filename)
        print(f"📚 Исходный словарь справочника сохранён: {filename}")
    else:
        print(f"⚠️ Файл {original_path} не найден, справочник не сохранён")


def export_fias_pairs_json(resolved_pairs, folder):
    pairs = [
        {
            "source_fias_id": pair["source"]["fias_id"],
            "target_fias_id": pair["target"]["fias_id"]
        }
        for pair in resolved_pairs
    ]
    path = os.path.join(folder, "resolved_fias_pairs.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    print(f"🧩 FIAS-пары сохранены: {path}")
