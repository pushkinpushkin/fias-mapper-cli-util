import os
from dadata import Dadata
from dotenv import load_dotenv


class DadataClient:
    def __init__(self):
        load_dotenv()

        self.api_token = os.getenv("DADATA_API_KEY")
        self.secret = os.getenv("DADATA_SECRET_KEY")

        if not self.api_token:
            raise RuntimeError("❌ DADATA API key is not set. Please define DADATA_API_KEY in your .env file.")

        self.client = Dadata(self.api_token, self.secret)
        self.check_limits()

    def check_limits(self):
        # Проверка лимитов
        try:
            balance = self.client.get_balance()
            stats = self.client.get_daily_stats()
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

    def suggest(self, param, normalized_name):
        result = self.client.suggest(param, normalized_name)
        return result

    def find_by_id(self, param, fias_id):
        return self.client.find_by_id(param, fias_id)
