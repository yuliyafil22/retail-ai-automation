#sinc_orders.py

import requests
import time
import os
from dotenv import load_dotenv

# Настройки RetailCRM
RETAILCRM_URL = os.getenv("RETAILCRM_URL")
RETAILCRM_APIKEY = os.getenv("RETAILCRM_APIKEY")

# Настройки Supabase
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

def sync_orders():
    print("🚀 Начинаем синхронизацию заказов...")

    # Получаем заказы из RetailCRM
    try:
        print("📥 Получаем заказы из RetailCRM...")
        response = requests.get(
            f"{RETAILCRM_URL}/api/v5/orders",
            params={'apiKey': RETAILCRM_API_KEY, 'limit': 100, 'page': 1}
        )

        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            print(f"✅ Найдено {len(orders)} заказов в RetailCRM")
        else:
            print(f"❌ Ошибка API RetailCRM: {response.status_code}")
            return

    except Exception as e:
        print(f"❌ Ошибка получения данных из RetailCRM: {e}")
        return

    # Настройки для Supabase REST API
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

    # Синхронизируем заказы
    success_count = 0
    error_count = 0

    for order in orders:
        try:
            # Подготавливаем данные для Supabase
            order_data = {
                'crm_id': order.get('id'),
                'first_name': order.get('firstName', ''),
                'last_name': order.get('lastName', ''),
                'phone': order.get('phone', ''),
                'email': order.get('email', ''),
                'total_sum': float(order.get('totalSumm', 0)),
                'status': order.get('status', 'new')
            }

            # Проверяем, есть ли уже такой заказ
            check_url = f"{SUPABASE_URL}/rest/v1/retailcrm_orders?crm_id=eq.{order.get('id')}&select=id"
            check_response = requests.get(check_url, headers=headers)

            if check_response.status_code == 200:
                existing_orders = check_response.json()

                if len(existing_orders) == 0:
                    # Вставляем новый заказ
                    insert_url = f"{SUPABASE_URL}/rest/v1/retailcrm_orders"
                    insert_response = requests.post(
                        insert_url,
                        headers=headers,
                        json=order_data
                    )

                    if insert_response.status_code == 201:
                        print(
                            f"✅ Заказ {order.get('id')} ({order.get('firstName')} {order.get('lastName')}) синхронизирован")

                        success_count += 1
                    else:
                        print(f"❌ Ошибка вставки заказа {order.get('id')}: {insert_response.status_code}")
                        print(f"   Ответ: {insert_response.text}")
                        error_count += 1
                else:
                    print(f"⏭️ Заказ {order.get('id')} уже существует")
            else:
                print(f"❌ Ошибка проверки заказа {order.get('id')}: {check_response.status_code}")
                print(f"   Ответ: {check_response.text}")
                error_count += 1

        except Exception as e:
            print(f"❌ Ошибка обработки заказа {order.get('id', 'неизвестен')}: {e}")
            error_count += 1

    # Итоговая статистика
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТ СИНХРОНИЗАЦИИ:")
    print(f"✅ Успешно синхронизировано: {success_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📦 Всего обработано: {len(orders)}")

    # Проверяем общее количество в Supabase
    try:
        count_url = f"{SUPABASE_URL}/rest/v1/retailcrm_orders?select=id"
        count_response = requests.get(count_url, headers=headers)
        if count_response.status_code == 200:
            total_orders = len(count_response.json())
            print(f"🗄️ Всего заказов в Supabase: {total_orders}")
    except Exception as e:
        print(f"❌ Ошибка подсчета: {e}")

if __name__ == "__main__":
    sync_orders()