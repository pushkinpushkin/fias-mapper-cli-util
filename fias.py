import time
import logging
from dadata_adapter import dadata
from fias_cache import FiasCache
from data_loader import load_json_or_empty

logger = logging.getLogger(__name__)

# Очистка кеша при устаревании
fias_cache = FiasCache()
if fias_cache.is_stale():
    fias_cache.cache.clear()


def normalize_city_name(name: str) -> str:
    name = name.strip().lower()
    name = name.replace("г.", "").replace("г ", "")
    name = name.replace(" - ", "-")
    name = name.replace("область", "").replace("край", "")
    name = name.replace("респ", "").replace("республика", "")
    name = name.replace("(", "").replace(")", "")
    return name.strip()


def get_fias_id(city_name):
    if not city_name:
        return None

    city_aliases = load_json_or_empty("exceptions/city_aliases.json")
    city_to_fias = load_json_or_empty("exceptions/city_to_fias.json")

    original_name = city_name.strip()
    original_name = city_aliases.get(original_name, original_name)
    normalized_name = normalize_city_name(original_name)

    if len(normalized_name) > 300:
        logger.warning(f"❌ Пропуск: '{normalized_name}' слишком длинное (>300 символов)")
        return

    if normalized_name in ("", "nan", "-", "none"):
        logger.warning(f"❌ Непригодное имя города: '{normalized_name}'")
        return None

    # 1. Проверка в словаре переопределений
    if original_name in city_to_fias:
        fias_id = city_to_fias[original_name]
        fias_cache.cache[original_name] = fias_id
        fias_cache.save()
        return fias_id

    # 2. Проверка в кеше
    if original_name in fias_cache.cache:
        return fias_cache.cache[original_name]

    try:
        time.sleep(0.05)
        result = dadata.suggest("address", normalized_name)

        if result:
            for suggestion in result:
                data = suggestion.get("data", {})
                fias_level = data.get("fias_level")

                if fias_level not in ("1", "3", "4", "6"):
                    continue

                if data.get("city") and data.get("settlement") and data[
                    "settlement"].strip().lower() == normalized_name:
                    fias_id = data.get("settlement_fias_id")
                    if fias_id:
                        fias_cache.cache[original_name] = fias_id
                        fias_cache.save()
                        return fias_id

                if data.get("city") and data["city"].strip().lower() == normalized_name:
                    fias_id = data.get("city_fias_id")
                    if fias_id:
                        fias_cache.cache[original_name] = fias_id
                        fias_cache.save()
                        return fias_id

                if not data.get("city") and data.get("settlement") and data[
                    "settlement"].strip().lower() == normalized_name:
                    fias_id = data.get("settlement_fias_id")
                    if fias_id:
                        fias_cache.cache[original_name] = fias_id
                        fias_cache.save()
                        return fias_id

        logger.warning(
            f"⚠️ Город/поселение '{original_name}' не найден. Похожий: {result[0]['value'] if result else '—'}")
    except Exception as e:
        logger.error(f"🚨 Ошибка при получении FIAS ID для '{original_name}': {e}")

    return None


def get_suggestion_hint(city_name):
    original_name = city_name.strip()
    normalized_name = normalize_city_name(original_name)

    if "_suggests" not in fias_cache.cache:
        fias_cache.cache["_suggests"] = {}

    if original_name in fias_cache.cache["_suggests"]:
        return fias_cache.cache["_suggests"][original_name]

    try:
        time.sleep(0.05)
        result = dadata.suggest("address", normalized_name)

        if result:
            for suggestion in result:
                data = suggestion.get("data", {})
                fias_level = data.get("fias_level")

                if fias_level in ("4", "6"):
                    hint = suggestion.get("unrestricted_value")
                    fias_cache.cache["_suggests"][original_name] = hint
                    fias_cache.save()
                    return hint

            # Если ничего не подошло по уровню
            hint = "нет совпадений с подходящим типом"
        else:
            hint = "нет совпадений"

        fias_cache.cache["_suggests"][original_name] = hint
        fias_cache.save()
        return hint

    except Exception as e:
        logger.error(f"🚨 Ошибка при получении подсказки для '{original_name}': {e}")
        return None


def get_city_name_by_fias_id(fias_id):
    if not fias_id:
        return None

    if fias_id in fias_cache.cache:
        return fias_cache.cache[fias_id]

    try:
        time.sleep(0.05)
        result = dadata.find_by_id("address", fias_id)
        if result:
            name = result[0].get("value")
            if name:
                fias_cache.cache[fias_id] = name
                fias_cache.save()
                return name
    except Exception as e:
        logger.error(f"🚨 Ошибка при получении имени по FIAS ID '{fias_id}': {e}")

    return None
