import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment
env_path = Path('.env')
load_dotenv(env_path)

RETAILCRM_URL = os.getenv("RETAILCRM_URL")
RETAILCRM_APIKEY = os.getenv("RETAILCRM_API_KEY")


def check_webhooks():
    print("🔍 Проверка webhook'ов через API...")

    if not RETAILCRM_URL or not RETAILCRM_APIKEY:
        print("❌ RetailCRM credentials not found")
        return

    try:
        # Проверяем существующие webhook'и
        params = {'apiKey': RETAILCRM_APIKEY}

        response = requests.get(
            f"{RETAILCRM_URL}/api/v5/integration-modules",
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API доступен")
            print(f"📊 Ответ: {data}")
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")

        # Попробуем получить информацию о webhook'ах
        webhook_response = requests.get(
            f"{RETAILCRM_URL}/api/v5/webhooks",
            params=params,
            timeout=30
        )

        if webhook_response.status_code == 200:
            webhook_data = webhook_response.json()
            print(f"🎯 Webhook'и найдены: {webhook_data}")
        else:
            print(f"❌ Webhook API error: {webhook_response.status_code}")
            print(f"Response: {webhook_response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


def check_api_methods():
    """Проверяем доступные методы API"""
    print("\n🔍 Проверка доступных методов API...")

    try:
        params = {'apiKey': RETAILCRM_APIKEY}

        # Проверяем базовую информацию
        response = requests.get(
            f"{RETAILCRM_URL}/api/v5/reference/sites",
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API работает")
            print(f"📊 Сайты: {data}")
        else:
            print(f"❌ API error: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_webhooks()
    check_api_methods()