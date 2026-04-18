import sys
import requests  # ИСПРАВЛЕНО: добавлен импорт requests
from pathlib import Path

current_dir = Path(__file__).parent
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

from integrations.supabase_client import SupabaseClient


def check_orders():
    print("🔍 Анализ заказов в ai_orders...")

    supabase = SupabaseClient()

    if not supabase.headers:
        print("❌ Supabase не настроен")
        return

    try:
        # Получаем все заказы
        url = f"{supabase.url}/rest/v1/{supabase.table_name}"
        params = {'select': 'crm_id,first_name,last_name,total_sum,ai_analysis', 'limit': 100}

        response = requests.get(url, headers=supabase.headers, params=params)

        if response.status_code == 200:
            orders = response.json()

            print(f"📊 Всего заказов: {len(orders)}")
            print("\n📋 Последние 10 заказов:")

            # Сортируем по crm_id
            sorted_orders = sorted(orders, key=lambda x: x.get('crm_id', 0), reverse=True)

            for i, order in enumerate(sorted_orders[:10], 1):
                crm_id = order.get('crm_id')
                name = f"{order.get('first_name', '')} {order.get('last_name', '')}"
                total = order.get('total_sum', 0)
                ai_category = order.get('ai_analysis', {}).get('customer_category', 'unknown')

                # Выделяем тестовые заказы
                if crm_id >= 888888:
                    print(f"   {i:2d}. 🧪 #{crm_id} - {name} - {total:,.0f} ₸ - {ai_category} (ТЕСТ)")
                else:
                    print(f"   {i:2d}. 📦 #{crm_id} - {name} - {total:,.0f} ₸ - {ai_category}")

            # Анализ по категориям AI
            print("\n🤖 Анализ по категориям AI:")
            categories = {}
            test_orders = 0
            migrated_orders = 0

            for order in orders:
                ai_data = order.get('ai_analysis', {})
                category = ai_data.get('customer_category', 'unknown')

                if order.get('crm_id', 0) >= 888888:
                    test_orders += 1
                elif category == 'migrated':
                    migrated_orders += 1

                categories[category] = categories.get(category, 0) + 1

            for category, count in categories.items():
                emoji = {'migrated': '📦', 'VIP': '⭐', 'regular': '👤', 'new': '🆕', 'постоянный': '👤'}.get(category, '❓')
                print(f"   {emoji} {category}: {count}")

            print(f"\n📊 Итоговая статистика:")
            print(f"   📦 Мигрированных: {migrated_orders}")
            print(f"   🧪 Тестовых: {test_orders}")
            print(f"   📈 Реальных: {len(orders) - test_orders}")

        else:
            print(f"❌ Ошибка получения заказов: {response.status_code}")


    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    check_orders()