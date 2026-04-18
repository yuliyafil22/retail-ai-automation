import os
from pathlib import Path
from dotenv import load_dotenv

# Проверяем .env
env_path = Path('.env')
print(f"📁 .env файл существует: {env_path.exists()}")

if env_path.exists():
    print(f"📄 Размер .env файла: {env_path.stat().st_size} байт")

    # Загружаем переменные
    load_dotenv(env_path)

    # Проверяем ключевые переменные
    variables = [
        'RETAILCRM_URL',
        'RETAILCRM_APIKEY',
        'NEXT_PUBLIC_SUPABASE_URL',
        'NEXT_PUBLIC_SUPABASE_ANON_KEY',
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]

    print("\n🔍 Проверка переменных:")
    for var in variables:
        value = os.getenv(var)
        if value:
            # Показываем только первые 10 символов для безопасности
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: НЕ НАЙДЕНА")

    # Тест простого импорта
    print("\n📦 Тест импортов:")
    try:
        import sys

        sys.path.insert(0, 'src')

        from src.config.settings import settings

        print("✅ settings импортирован")

        from src.integrations import TelegramClient

        print("✅ TelegramClient импортирован")

        from src.integrations.supabase_client import SupabaseClient

        print("✅ SupabaseClient импортирован")

        from src.ai.analyzer import OrderAnalyzer

        print("✅ OrderAnalyzer импортирован")

    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")

else:
    print("❌ .env файл не найден!")
    print("Создай .env файл в корне проекта с твоими ключами")