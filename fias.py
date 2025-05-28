import time
import logging
from dadata_adapter import dadata
from fias_cache import FiasCache

logger = logging.getLogger(__name__)

# Очистка кеша при устаревании
cache = FiasCache()
if cache.is_stale():
    cache.cache.clear()

city_aliases = {
    "Московская область": "Москва",
    "МОСКВА ВОСТОК": "Москва",
    "МОСКВА ЮГ": "Москва",
    "МОСКВА СЕВЕР": "Москва",
    "МОСКВА ЗАПАД": "Москва",
    "КОРОЛЕВ": "Королёв",
    "Ростов": "Ростов Великий",
    "ОРЕЛ": "Орёл",
    "ЩЕЛКОВО": "Щёлково"
}

city_to_fias = {
    "Благовещенск": "8f41253d-6e3b-48a9-842a-25ba894bd093",  # Дальневосточный
    "Благовещенск (Уфа)": "da7ef573-cdbe-458e-a790-b29ad3a3d140",  # Уральский
    "Троицк": "b5ad78c2-cc8f-4769-9a9f-75743d8da02f",  # Уральский
    "Троицк (Москва)": "7dde11f6-f6ab-4a05-8052-78e0cab8fc59",  # Москва
    "Мирный (Архангельск)": "977c7606-1b37-4424-84f7-b0c66c3e4b94",  # Архангельская область
    "Мирный (Якутск)": "62d403af-d460-4e79-a90b-8b6a351af3b1",  # Дальневосточный Республика Саха (Якутия)
    "Березовский": "adf5df2b-2c2e-45a9-b971-05550353cf43",  # Уральский
    "Березовский (Кемерово)": "ef6bac92-b712-42ba-942b-515b36b9a32c"  # Сибирский
}


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

    original_name = city_name.strip()
    original_name = city_aliases.get(original_name, original_name)
    normalized_name = normalize_city_name(original_name)

    if len(normalized_name) > 300:
        logger.warning(f"❌ Пропуск: '{normalized_name}' слишком длинное (>300 символов)")
        return None

    if normalized_name in ("", "nan", "-", "none"):
        logger.warning(f"❌ Непригодное имя города: '{normalized_name}'")
        return None

    # 1. Проверка в словаре переопределений
    if original_name in city_to_fias:
        fias_id = city_to_fias[original_name]
        cache.cache[original_name] = fias_id
        cache.save()
        return fias_id

    # 2. Проверка в кеше
    if original_name in cache.cache:
        return cache.cache[original_name]

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
                        cache.cache[original_name] = fias_id
                        cache.save()
                        return fias_id

                if data.get("city") and data["city"].strip().lower() == normalized_name:
                    fias_id = data.get("city_fias_id")
                    if fias_id:
                        cache.cache[original_name] = fias_id
                        cache.save()
                        return fias_id

                if not data.get("city") and data.get("settlement") and data[
                    "settlement"].strip().lower() == normalized_name:
                    fias_id = data.get("settlement_fias_id")
                    if fias_id:
                        cache.cache[original_name] = fias_id
                        cache.save()
                        return fias_id

        logger.warning(
            f"⚠️ Город/поселение '{original_name}' не найден. Похожий: {result[0]['value'] if result else '—'}")
    except Exception as e:
        logger.error(f"🚨 Ошибка при получении FIAS ID для '{original_name}': {e}")

    return None


def get_suggestion_hint(city_name):
    original_name = city_name.strip()
    normalized_name = normalize_city_name(original_name)

    if "_suggests" not in cache.cache:
        cache.cache["_suggests"] = {}

    if original_name in cache.cache["_suggests"]:
        return cache.cache["_suggests"][original_name]

    try:
        time.sleep(0.05)
        result = dadata.suggest("address", normalized_name)

        if result:
            for suggestion in result:
                data = suggestion.get("data", {})
                fias_level = data.get("fias_level")

                if fias_level in ("4", "6"):
                    hint = suggestion.get("unrestricted_value")
                    cache.cache["_suggests"][original_name] = hint
                    cache.save()
                    return hint

            # Если ничего не подошло по уровню
            hint = "нет совпадений с подходящим типом"
        else:
            hint = "нет совпадений"

        cache.cache["_suggests"][original_name] = hint
        cache.save()
        return hint

    except Exception as e:
        logger.error(f"🚨 Ошибка при получении подсказки для '{original_name}': {e}")
        return None


def get_city_name_by_fias_id(fias_id):
    if not fias_id:
        return None

    if fias_id in cache.cache:
        return cache.cache[fias_id]

    try:
        time.sleep(0.05)
        result = dadata.find_by_id("address", fias_id)
        if result:
            name = result[0].get("value")
            if name:
                cache.cache[fias_id] = name
                cache.save()
                return name
    except Exception as e:
        logger.error(f"🚨 Ошибка при получении имени по FIAS ID '{fias_id}': {e}")

    return None
