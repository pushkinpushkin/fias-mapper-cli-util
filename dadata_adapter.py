from dadata import Dadata
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Получаем токен из переменной окружения
API_TOKEN = os.getenv("DADATA_API_KEY")
SECRET = os.getenv("DADATA_SECRET_KEY")

if not API_TOKEN:
    raise RuntimeError("❌ DADATA API key is not set. Please define DADATA_API_KEY in your .env file.")

# Инициализируем клиента
dadata = Dadata(API_TOKEN, SECRET)

# Проверка лимитов
try:
    balance = dadata.get_balance()
    stats = dadata.get_daily_stats()
    used = stats["services"].get("suggestions", 0)
    remaining = stats["remaining"].get("suggestions", 0)

    print(f"💳 Баланс: {balance:.2f} ₽")
    print(f"🔍 DaData лимит: использовано {used}, осталось {remaining}")

    if remaining < 1000:
        print("⚠️ Осталось мало запросов для suggestions! Подумай о пополнении баланса.")
    if remaining == 0:
        raise RuntimeError("🚫 Лимит запросов suggestions исчерпан!")

except Exception as e:
    raise RuntimeError(f"❌ Ошибка при проверке лимитов DaData: {e}")
