# src/config/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Находим .env файл в корне проекта
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # src/config -> src -> корень
env_path = project_root / '.env'

print(f"Ищу .env файл в: {env_path}")
load_dotenv(env_path)


class Settings:
    # RetailCRM
    RETAILCRM_URL = os.getenv("RETAILCRM_URL")
    RETAILCRM_APIKEY = os.getenv("RETAILCRM_APIKEY")

    # Supabase
    SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # AI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Google Gemini (НОВЫЙ!)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

    # Webhook
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default-secret")

    def __init__(self):
        print("🔍 Загруженные переменные:")
        print(f"RETAILCRM_URL: {self.RETAILCRM_URL}")
        print(f"SUPABASE_URL: {self.SUPABASE_URL}")
        print(f"TELEGRAM_TOKEN: {'✅ Есть' if self.TELEGRAM_TOKEN else '❌ Нет'}")
        print(f"OPENAI_API_KEY: {'✅ Есть' if self.OPENAI_API_KEY else '❌ Нет'}")
        print(f"GEMINI_API_KEY: {'✅ Есть' if self.GEMINI_API_KEY else '❌ Нет'}")


settings = Settings()