import requests
import time
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# RetailCRM настройки
RETAILCRM_URL = os.getenv("RETAILCRM_URL")
RETAILCRM_APIKEY = os.getenv("RETAILCRM_APIKEY")

# Telegram настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

print("Содержимое last_order_id.txt:")

try:
    with open("last_order_id.txt", "r") as f:
        print(f.read())
except Exception as e:
    print("Файл не найден или ошибка чтения:", e)

LAST_ORDER_ID_FILE = "last_order_id.txt"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def get_last_order_id():
    try:
        with open(LAST_ORDER_ID_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def set_last_order_id(order_id):
    with open(LAST_ORDER_ID_FILE, "w") as f:
        f.write(str(order_id))

def check_new_orders():
    while True:
        last_order_id = get_last_order_id()  # <-- перемести сюда!
        try:
            resp = requests.get(
                f"{RETAILCRM_URL}/api/v5/orders",
                params={"apiKey": RETAILCRM_APIKEY, "limit": 100}
            )
            data = resp.json()
            orders = data.get("orders", [])
            new_max_id = last_order_id

            for order in orders:
                order_id = order.get("id")
                total_summ = order.get("totalSumm", 0)
                print(f"Проверяю заказ: id={order_id}, сумма={total_summ}, last_order_id={last_order_id}")
                if order_id is None:
                    continue
                if order_id > last_order_id and total_summ > 50000:

                    print("Отправляю уведомление!")
                    msg = (
                        f"🛒 <b>Новый заказ!</b>\n"
                        f"ФИО: {order.get('firstName', '')} {order.get('lastName', '')}\n"
                        f"Телефон: {order.get('phone', '')}\n"
                        f"Сумма: {int(total_summ):,} ₸\n"
                        f"ID заказа: {order_id}"
                    )
                    send_telegram_message(msg)
                if order_id and order_id > new_max_id:
                    new_max_id = order_id
            print(f"new_max_id после цикла: {new_max_id}")

            set_last_order_id(new_max_id)
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(60)  # Проверять раз в минуту

if __name__ == "__main__":
    check_new_orders()


