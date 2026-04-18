"""
RetailCRM → Supabase sync
Забирает заказы из RetailCRM и загружает в Supabase.
Таблица уже создана через SQL Editor.

Установка: pip install requests
Запуск:    python retailcrm_to_supabase.py
"""

import json
import time
import requests
import os
from dotenv import load_dotenv

RETAILCRM_URL = os.getenv("RETAILCRM_URL")
RETAILCRM_APIKEY = os.getenv("RETAILCRM_APIKEY")

SUPABASE_URL     = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY     = os.getenv("sNEXT_PUBLIC_SUPABASE_ANON_KEY")
TABLE_NAME       = "retailcrm_orders"

SUPABASE_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=merge-duplicates",
}


def fetch_orders_from_crm() -> list[dict]:
    all_orders = []
    page       = 1

    print("Загружаю заказы из RetailCRM...")

    while True:
        resp = requests.get(
            f"{RETAILCRM_URL}/api/v5/orders",
            params={"apiKey": RETAILCRM_APIKEY, "page": page, "limit": 100},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            raise RuntimeError(f"RetailCRM error: {data.get('errorMsg')}")

        orders = data.get("orders", [])
        all_orders.extend(orders)
        print(f"  Страница {page}: {len(orders)} заказов (всего: {len(all_orders)})")

        if page >= data.get("pagination", {}).get("totalPageCount", 1):
            break
        page += 1
        time.sleep(0.3)

    print(f"  Итого: {len(all_orders)} заказов\n")
    return all_orders


def map_order(order: dict) -> dict:
    items = [
        {
            "productName":  i.get("productName") or i.get("offer", {}).get("name"),
            "quantity":     i.get("quantity"),
            "initialPrice": i.get("initialPrice") or i.get("prices", [{}])[0].get("price"),
        }
        for i in order.get("items", [])
    ]

    address = order.get("delivery", {}).get("address", {})

    raw_cf = order.get("customFields", {})
    custom_fields = (
        {f["code"]: f.get("value") for f in raw_cf if "code" in f}
        if isinstance(raw_cf, list) else (raw_cf or {})
    )

    total_sum = sum((i.get("quantity") or 0) * (i.get("initialPrice") or 0) for i in items)

    return {
        "crm_id":           order.get("id"),
        "first_name":       order.get("firstName"),
        "last_name":        order.get("lastName"),
        "phone":            order.get("phone"),
        "email":            order.get("email"),
        "status":           order.get("status"),
        "order_type":       order.get("orderType"),
        "order_method":     order.get("orderMethod"),
        "items":            items,
        "delivery_city":    address.get("city"),
        "delivery_address": address.get("text"),
        "utm_source":       custom_fields.get("utm_source"),
        "total_sum":        total_sum or None,
        "synced_at":        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def clear_table(crm_ids: list[int]):
    """Удаляет из Supabase строки, которых больше нет в RetailCRM."""
    print("Очищаю устаревшие записи из Supabase...")

    # Получаем все crm_id которые сейчас есть в Supabase
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        headers={**SUPABASE_HEADERS, "Prefer": ""},
        params={"select": "crm_id", "limit": 10000},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"  Не удалось получить список из Supabase: {resp.text}")
        return

    existing_ids = {row["crm_id"] for row in resp.json() if row.get("crm_id")}
    actual_ids   = set(crm_ids)
    to_remove    = existing_ids - actual_ids

    if not to_remove:
        print("  Устаревших записей нет\n")
        return

    print(f"  Найдено устаревших записей: {len(to_remove)}, удаляю...")

    # Удаляем пачкой через in=(id1,id2,...)
    ids_str = f"({','.join(str(i) for i in to_remove)})"
    del_resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        headers={**SUPABASE_HEADERS, "Prefer": ""},
        params={"crm_id": f"in.{ids_str}"},
        timeout=30,
    )
    if del_resp.status_code in (200, 204):
        print(f"  Удалено {len(to_remove)} записей\n")
    else:
        print(f"  Ошибка при удалении: {del_resp.status_code} — {del_resp.text}\n")


def upsert_to_supabase(rows: list[dict]) -> tuple[int, int]:
    ok, err    = 0, 0
    batch_size = 50
    endpoint   = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        resp  = requests.post(
            endpoint,
            headers=SUPABASE_HEADERS,
            data=json.dumps(batch, ensure_ascii=False),
            timeout=30,
        )
        if resp.status_code in (200, 201):
            ok += len(batch)
            print(f"  Записано {ok} / {len(rows)}")
        else:
            err += len(batch)
            print(f"  Ошибка батча {i // batch_size + 1}: {resp.status_code} — {resp.text}")

    return ok, err


def main():
    print("=" * 55)
    print("  RetailCRM -> Supabase sync")
    print("=" * 55 + "\n")

    orders = fetch_orders_from_crm()
    if not orders:
        print("Заказов не найдено.")
        return

    crm_ids = [o["id"] for o in orders if o.get("id")]
    clear_table(crm_ids)

    rows = [map_order(o) for o in orders]
    print(f"Записываю {len(rows)} заказов в Supabase...")
    ok, err = upsert_to_supabase(rows)

    print("\n" + "=" * 55)
    print(f"  Успешно: {ok}   Ошибки: {err}")
    print("=" * 55)


if __name__ == "__main__":
    main()