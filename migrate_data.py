import sys
from pathlib import Path

# Добавляем src в путь (ИСПРАВЛЕНО: было scr)
current_dir = Path(__file__).parent
src_path = current_dir / 'src'  # ← ИСПРАВЛЕНО
sys.path.insert(0, str(src_path))

from integrations.supabase_client import SupabaseClient


def migrate_data():
    print("🚀 Миграция данных из retailcrm_orders в ai_orders...")

    supabase = SupabaseClient()

    # Проверяем новую таблицу
    print("🔍 Проверка новой таблицы...")
    structure = supabase.check_table_structure()
    print(f"Структура: {structure}")

    if structure.get('status') == 'ok':
        print("✅ Таблица ai_orders готова")

        # Запускаем миграцию
        print("\n📦 Начинаем миграцию данных...")
        result = supabase.migrate_data_from_retailcrm_orders()

        print(f"\n📊 Результат миграции:")
        print(f"✅ Мигрировано: {result.get('migrated', 0)}")
        print(f"❌ Ошибок: {result.get('errors', 0)}")
        print(f"📦 Всего: {result.get('total', 0)}")

        if result.get('error'):
            print(f"❌ Ошибка: {result['error']}")
    else:
        print("❌ Таблица ai_orders не готова")
        print("Выполни SQL скрипт в Supabase Dashboard сначала!")


if __name__ == "__main__":
    migrate_data()