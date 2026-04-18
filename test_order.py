# test_order.py - РАБОЧАЯ ВЕРСИЯ

import requests
import json
import time
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Настройки RetailCRM
RETAILCRM_URL = os.getenv("RETAILCRM_URL")
RETAILCRM_API_KEY = os.getenv("RETAILCRM_API_KEY")

# Проверяем наличие настроек
if not RETAILCRM_URL or not RETAILCRM_API_KEY:
    print("❌ Ошибка: Не настроены RETAILCRM_URL или RETAILCRM_API_KEY в .env файле")
    exit(1)

# Правильный эндпоинт (из документации)
base_url = f"{RETAILCRM_URL}/api/v5/orders/create"


# ============================================================
# ФУНКЦИЯ ДЛЯ ОТПРАВКИ ЗАКАЗА
# ============================================================
def send_order(order_data, order_name):
    """Отправляет один заказ в RetailCRM"""

    print(f"\n{'=' * 60}")
    print(f"📦 Отправка заказа: {order_name}")
    print(f"{'=' * 60}")

    # Считаем сумму
    total_sum = sum(item['initialPrice'] * item['quantity'] for item in order_data['items'])
    print(f"👤 Клиент: {order_data['firstName']} {order_data['lastName']}")
    print(f"💰 Сумма: {total_sum:,} ₸")

    # Формируем данные для отправки
    payload = {
        'apiKey': RETAILCRM_API_KEY,
        'order': json.dumps(order_data, ensure_ascii=False)  # Важно: order должен быть JSON строкой!
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.post(
            base_url,
            data=payload,  # data, а не json
            headers=headers,
            timeout=30
        )

        print(f"📡 URL: {base_url}")
        print(f"📡 Статус: {response.status_code}")

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Заказ успешно создан!")
            if 'id' in result:
                print(f"   ID заказа в CRM: {result['id']}")
            return True
        else:
            print(f"❌ Ошибка: HTTP {response.status_code}")
            print(f"   Ответ: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


# ============================================================
# ТЕСТОВЫЕ ЗАКАЗЫ
# ============================================================

# ТЕСТ 1: Средний заказ с рискованным комментарием
order_medium_risk = {
    "firstName": "Айнурррррр7",
    "lastName": "Тестировщик",
    "phone": "+77770000101",
    "email": "test.medium21@example.com",
    "orderType": "eshop-individual",
    "orderMethod": "shopping-cart",
    "status": "new",
    "customerComment": "Очень хочу получить заказ, но сомневаюсь, что товар подойдет по размеру. Если что, верну обратно. Есть ли у вас гарантия возврата?",
    "items": [
        {
            "productName": "Утягивающий комбидресс Nova Slim",
            "quantity": 1,
            "initialPrice": 28000
        },
        {
            "productName": "Корректирующее бельё Nova Classic",
            "quantity": 2,
            "initialPrice": 15000
        }
    ],
    "delivery": {
        "address": {
            "city": "Алматы",
            "text": "ул. Абая 150, кв 12"
        }
    },
    "customFields": {
        "utm_source": "test_api"
    }
}

# ТЕСТ 2: VIP заказ
order_vip = {
    "firstName": "Вип5",
    "lastName": "Клиенттттт",
    "phone": "+77770000102",
    "email": "test.vip12@example.com",
    "orderType": "eshop-individual",
    "orderMethod": "shopping-cart",
    "status": "new",
    "customerComment": "",
    "items": [
        {
            "productName": "Утягивающее боди Nova Body",
            "quantity": 3,
            "initialPrice": 35000
        },
        {
            "productName": "Утягивающий комбидресс Nova Slim",
            "quantity": 2,
            "initialPrice": 28000
        }
    ],
    "delivery": {
        "address": {
            "city": "Астана",
            "text": "пр. Туран 45, кв 15"
        }
    },
    "customFields": {
        "utm_source": "test_api"
    }
}

# ТЕСТ 3: Проблемный заказ
order_problem = {
    "firstName": "Проблемныййд",
    "lastName": "Клиент",
    "phone": "+77770000103",
    "email": "test.problem12@example.com",
    "orderType": "eshop-individual",
    "orderMethod": "shopping-cart",
    "status": "new",
    "customerComment": "В прошлый раз пришел сильно бракованный товар! Очень сильно прям недоволен качеством. Хочу вернуть деньги срочно.",
    "items": [
        {
            "productName": "Бюстье корректирующее Nova Lift",
            "quantity": 1,
            "initialPrice": 22000
        }
    ],
    "delivery": {
        "address": {
            "city": "Алматы",
            "text": "ул. Жандосова 58, кв 21"
        }
    },
    "customFields": {
        "utm_source": "test_api"
    }
}

# ТЕСТ 4: Маленький заказ
order_small = {
    "firstName": "Новыййн",
    "lastName": "Клиент",
    "phone": "+77770000104",
    "email": "test.small12@example.com",
    "orderType": "eshop-individual",
    "orderMethod": "shopping-cart",
    "status": "new",
    "customerComment": "",
    "items": [
        {
            "productName": "Корректирующие шорты Nova Shape",
            "quantity": 1,
            "initialPrice": 12000
        }
    ],
    "delivery": {
        "address": {
            "city": "Алматы",
            "text": "ул. Толе би 220, кв 65"
        }
    },
    "customFields": {
        "utm_source": "test_api"
    }
}


# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("🚀 ЗАГРУЗКА ТЕСТОВЫХ ЗАКАЗОВ В RETAILCRM")
    print("=" * 60)
    print(f"📡 URL RetailCRM: {RETAILCRM_URL}")
    print(f"📡 Эндпоинт: {base_url}")
    print("=" * 60)

    # Сначала проверим подключение
    print("\n🔍 Проверка подключения...")
    try:
        test_response = requests.get(
            f"{RETAILCRM_URL}/api/v5/credentials",
            params={"apiKey": RETAILCRM_API_KEY},
            timeout=10
        )
        if test_response.status_code == 200:
            print("✅ API ключ работает!")
        else:
            print(f"⚠️ API ключ вернул статус {test_response.status_code}")
    except Exception as e:
        print(f"⚠️ Не удалось проверить ключ: {e}")

    orders = [
        (order_medium_risk, "🔶 ТЕСТ 1: Средний заказ + рискованный комментарий"),
        (order_vip, "⭐ ТЕСТ 2: VIP заказ (большая сумма)"),
        (order_problem, "⚠️ ТЕСТ 3: Проблемный заказ (негативный комментарий)"),
        (order_small, "🆕 ТЕСТ 4: Маленький заказ (новый клиент)")
    ]

    success_count = 0
    for order_data, order_name in orders:
        if send_order(order_data, order_name):
            success_count += 1
        time.sleep(2)

    print("\n" + "=" * 60)
    print("📊 ИТОГИ ЗАГРУЗКИ")
    print("=" * 60)
    print(f"✅ Успешно: {success_count} из {len(orders)}")

    if success_count > 0:
        print("\n🔔 Ждите уведомления в Telegram через 1-3 минуты")
    else:
        print("\n⚠️ Заказы не созданы.")
        print("\n👉 Альтернатива: создайте заказ вручную в админке RetailCRM:")
        print("   1. Откройте https://yulverkz.retailcrm.ru/admin")
        print("   2. Заказы → Добавить заказ")
        print("   3. Заполните поля и сохраните")

    print("=" * 60)


if __name__ == "__main__":
    main()