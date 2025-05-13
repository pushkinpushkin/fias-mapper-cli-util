import argparse
import os
import pandas as pd
from fias import get_fias_id, get_suggestion_hint, get_city_name_by_fias_id
from report import create_report_folder, save_excel_report, save_json_report, save_source_excel, save_current_dict_json, \
    export_fias_pairs_json
from data_loader import load_existing_mappings
import subprocess
import platform


def extract_pairs_from_excel(filepath):
    df = pd.read_excel(filepath)
    pairs = []
    for _, row in df.iterrows():
        try:
            source = str(row.iloc[2]).strip()  # Третья колонка
            target = str(row.iloc[5]).strip()  # Шестая колонка
            if source and target:
                pairs.append((source, target))
        except Exception as e:
            print(f"Ошибка при разборе строки: {e}")
    return pairs


def remove_duplicate_pairs(pairs):
    seen = set()
    unique = []
    for source, target in pairs:
        key = (source.strip().lower(), target.strip().lower())
        if key not in seen:
            seen.add(key)
            unique.append((source, target))
    return unique


def remove_self_mappings(pairs):
    return [
        pair for pair in pairs
        if pair["source"]["fias_id"] != pair["target"]["fias_id"]
    ]


def resolve_fias_pairs(raw_pairs):
    resolved = []

    for source, target in raw_pairs:
        source_id = get_fias_id(source)
        target_id = get_fias_id(target)

        if source_id and target_id:
            resolved.append({
                "source": {"name": source, "fias_id": source_id},
                "target": {"name": target, "fias_id": target_id}
            })
        else:
            if not source_id:
                hint = get_suggestion_hint(source)
                print(f"⚠️ Город '{source}' не найден. Похожий: {hint}")
            if not target_id:
                hint = get_suggestion_hint(target)
                print(f"⚠️ Город '{target}' не найден. Похожий: {hint}")
            print(f"❗️ Пропущено: {source} → {source_id}, {target} → {target_id}")

    return resolved


def compare_with_existing(new_data, existing_data):
    existing_map = {
        entry["source"]["fias_id"]: entry["target"]["fias_id"]
        for entry in existing_data
    }

    to_insert = []
    to_update = []
    seen_sources = set()

    for item in new_data:
        src = item["source"]["fias_id"]
        tgt = item["target"]["fias_id"]
        seen_sources.add(src)

        if src not in existing_map:
            to_insert.append(item)
        elif existing_map[src] != tgt:
            to_update.append(item)

    # Дополняем to_delete, вытягивая name если есть
    to_delete = []
    for entry in existing_data:
        source_id = entry["source"]["fias_id"]
        target_id = entry["target"]["fias_id"]
        source_name = get_city_name_by_fias_id(source_id)
        target_name = get_city_name_by_fias_id(target_id)
        if source_id not in seen_sources:
            to_delete.append({
                "source": {
                    "fias_id": source_id,
                    "name": source_name
                },
                "target": {
                    "fias_id": target_id,
                    "name": target_name
                }
            })

    return to_insert, to_update, to_delete


def main():
    parser = argparse.ArgumentParser(description="Сравнение справочника городов с Excel")
    parser.add_argument("--input", required=True, help="Excel-файл с парами городов")
    parser.add_argument("--existing", required=True, help="JSON-файл с clientCityId / targetCityId")
    parser.add_argument("--report", action="store_true", help="Сохранить Excel и JSON-отчёты")
    parser.add_argument("--open", action="store_true", help="Открыть папку с отчётами после выполнения")
    args = parser.parse_args()

    raw_pairs = extract_pairs_from_excel(args.input)
    raw_pairs = remove_duplicate_pairs(raw_pairs)
    resolved_pairs = resolve_fias_pairs(raw_pairs)
    resolved_pairs = remove_self_mappings(resolved_pairs)
    existing = load_existing_mappings(args.existing)

    if not args.report:
        return

    generate_fias_mapping_report(args, existing, resolved_pairs)


def open_report_folder(path):
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", path])
        elif system == "Windows":
            subprocess.run(["explorer", path])
        elif system == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            print(f"❗️ Неизвестная ОС, не удалось открыть папку: {path}")
    except Exception as e:
        print(f"❌ Ошибка при открытии папки: {e}")


def save_all_reports(to_insert, to_update, to_delete, resolved_pairs, args, folder):
    save_excel_report(to_insert, folder, "to_insert")
    save_excel_report(to_update, folder, "to_update")
    save_excel_report(to_delete, folder, "to_delete")
    save_json_report(to_insert, folder, "to_insert")
    save_json_report(to_update, folder, "to_update")
    save_json_report(to_delete, folder, "to_delete")
    export_fias_pairs_json(resolved_pairs, folder)
    save_source_excel(args.input, folder)
    save_current_dict_json(args.existing, folder)


def generate_fias_mapping_report(args, existing, resolved_pairs):
    to_insert, to_update, to_delete = compare_with_existing(resolved_pairs, existing)

    print(f"➕ Новых записей: {len(to_insert)}")
    print(f"♻️ Требуют обновления: {len(to_update)}")
    print(f"🗑 Удалить: {len(to_delete)}")

    folder = create_report_folder()
    save_all_reports(to_insert, to_update, to_delete, resolved_pairs, args, folder)

    abs_path = os.path.abspath(folder)
    print(f"📂 Отчёты сохранены в папку: {abs_path}")

    if args.open:
        open_report_folder(abs_path)


if __name__ == "__main__":
    main()
