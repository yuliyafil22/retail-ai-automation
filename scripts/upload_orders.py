import json
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("RETAILCRM_URL")
API_KEY  = os.getenv("RETAILCRM_API_KEY")
SITE     = os.getenv("RETAILCRM_SITE")
ENDPOINT = f"{BASE_URL}/api/v5/orders/create"

def get_existing_phones() -> set:
    """Возвращает set телефонов уже существующих заказов — чтобы не дублировать."""
    phones = set()
    page   = 1
    while True:
        resp = requests.get(
            f"{BASE_URL}/api/v5/orders",
            params={"apiKey": API_KEY, "page": page, "limit": 100},
            timeout=15,
        )
        if resp.status_code != 200:
            break
        data   = resp.json()
        orders = data.get("orders", [])
        for o in orders:
            phone = o.get("phone") or o.get("customer", {}).get("phones", [{}])[0].get("number")
            if phone:
                phones.add(phone)
        if page >= data.get("pagination", {}).get("totalPageCount", 1):
            break
        page += 1

        time.sleep(0.2)
    return phones

# ── Загрузка заказов из файла ──────────────────────────────────────────────
with open("../mock_orders.json", "r", encoding="utf-8") as f:
    orders = json.load(f)

print(f"Загружено из файла: {len(orders)} заказов")

existing_phones = get_existing_phones()
print(f"Уже в CRM (по телефону): {len(existing_phones)} заказов")
print("-" * 50)

success_count = 0
skip_count    = 0
error_count   = 0
errors        = []

for i, order in enumerate(orders, 1):
    phone = order.get("phone", "")

    # Пропускаем дубликаты
    if phone in existing_phones:
        print(f"[{i:02d}] ⏭  {order['firstName']} {order['lastName']} — уже есть, пропускаю")
        skip_count += 1
        continue

    # Считаем сумму заказа
    total_summ = sum(
        item.get("initialPrice", 0) * item.get("quantity", 1)
        for item in order.get("items", [])
    )

    # Структура заказа — customer привязывает заказ к клиенту
    order_data = {
        "status":      order.get("status", "new"),
        "orderType":   order.get("orderType", "eshop-individual"),
        "orderMethod": order.get("orderMethod", "shopping-cart"),
        "site":        SITE,
        "summ":        total_summ,

        # Клиент — CRM создаст или найдёт по телефону
        "firstName": order.get("firstName", ""),
        "lastName":  order.get("lastName",  ""),
        "phone":     phone,
        "email":     order.get("email", ""),
        "customer": {
            "firstName": order.get("firstName", ""),
            "lastName":  order.get("lastName",  ""),
            "phones":    [{"number": phone}],
            "email":     order.get("email", ""),
        },

        # Товарные позиции
        "items": [
            {
                "productName":  item.get("productName", ""),
                "quantity":     item.get("quantity", 1),
                "initialPrice": item.get("initialPrice", 0),
                "purchasePrice": item.get("initialPrice", 0),
            }
            for item in order.get("items", [])
        ],

        # Доставка
        "delivery": {
            "address": order.get("delivery", {}).get("address", {}),
        },

        # UTM и кастомные поля
        "customFields": order.get("customFields", {}),
    }

    payload = {
        "order":  json.dumps(order_data, ensure_ascii=False),
        "apiKey": API_KEY,
        "site":   SITE,
    }

    try:
        response = requests.post(ENDPOINT, data=payload, timeout=15)
        result   = response.json()

        if response.status_code == 201 and result.get("success"):
            success_count += 1
            existing_phones.add(phone)
            order_id = result.get("id", "—")
            print(f"[{i:02d}] ✅ {order['firstName']} {order['lastName']} | {total_summ:,} ₸ → ID: {order_id}")
        else:
            error_count += 1
            err_msg = result.get("errorMsg") or str(result.get("errors", result))
            errors.append({"order": i, "name": f"{order['firstName']} {order['lastName']}", "error": err_msg})
            print(f"[{i:02d}] ❌ {order['firstName']} {order['lastName']} → {err_msg}")

    except requests.exceptions.RequestException as e:
        error_count += 1
        errors.append({"order": i, "name": f"{order['firstName']} {order['lastName']}", "error": str(e)})
        print(f"[{i:02d}] ❌ Сетевая ошибка: {e}")

    time.sleep(0.3)

# ── Итог ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("ИТОГ:")
print(f"  ✅ Успешно загружено: {success_count}")
print(f"  ⏭  Пропущено (дубли): {skip_count}")
print(f"  ❌ С ошибками:        {error_count}")
if errors:
    print("\nДетали ошибок:")
    for e in errors:
        print(f"  #{e['order']} {e['name']}: {e['error']}")