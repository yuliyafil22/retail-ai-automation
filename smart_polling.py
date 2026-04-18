# smart_polling.py - Полная версия с AI анализом и полными уведомлениями

import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Setup
current_dir = Path(__file__).parent
src_path = current_dir / 'src'
env_path = current_dir / '.env'

sys.path.insert(0, str(src_path))
load_dotenv(env_path)

from integrations.supabase_client import SupabaseClient
from integrations.telegram import TelegramClient
from ai.analyzer import OrderAnalyzer


class SmartPolling:
    def __init__(self):
        self.supabase = SupabaseClient()
        self.telegram = TelegramClient()
        self.analyzer = OrderAnalyzer()

        # RetailCRM settings
        self.retailcrm_url = os.getenv("RETAILCRM_URL")
        self.retailcrm_key = os.getenv("RETAILCRM_API_KEY")

        print(f"🔧 Smart Polling initialized")
        print(f"📡 RetailCRM: {self.retailcrm_url}")
        print(f"🗄️ Supabase: {'✅' if self.supabase.url else '❌'}")
        print(f"📱 Telegram: {'✅' if self.telegram.token else '❌'}")

    def get_max_order_id_from_ai_orders(self):
        """Получаем максимальный ID заказа из нашей таблицы"""
        try:
            url = f"{self.supabase.url}/rest/v1/{self.supabase.table_name}"
            params = {
                'select': 'crm_id',
                'order': 'crm_id.desc',
                'limit': 1
            }

            response = requests.get(url, headers=self.supabase.headers, params=params)

            if response.status_code == 200:
                orders = response.json()
                if orders:
                    max_id = orders[0].get('crm_id', 0)
                    # Исключаем тестовые заказы
                    if max_id >= 888888:
                        # Получаем второй по величине ID
                        params['limit'] = 10
                        response = requests.get(url, headers=self.supabase.headers, params=params)
                        if response.status_code == 200:
                            all_orders = response.json()
                            for order in all_orders:
                                order_id = order.get('crm_id', 0)
                                if order_id < 888888:
                                    return order_id
                    return max_id
                else:
                    return 0
            else:
                return 0
        except Exception as e:
            print(f"❌ Error getting max order ID: {e}")
            return 0

    def get_new_orders_from_crm(self, last_order_id):
        """Получаем новые заказы из RetailCRM"""
        try:
            params = {
                'apiKey': self.retailcrm_key,
                'limit': 100,
                'page': 1
            }

            response = requests.get(
                f"{self.retailcrm_url}/api/v5/orders",
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                orders = data.get('orders', [])

                # Фильтруем только новые заказы
                new_orders = []
                for order in orders:
                    order_id = order.get('id', 0)
                    if order_id > last_order_id:
                        new_orders.append(order)

                return new_orders
            else:
                print(f"❌ RetailCRM API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error getting orders from CRM: {e}")
            return []

    def process_new_order(self, order):
        """Обрабатываем новый заказ"""
        order_id = order.get('id')

        print(f"🆕 Processing new order: {order_id}")

        # AI analysis
        ai_analysis = self.analyzer.analyze_order(order)

        # Безопасно достаём delivery_city и delivery_address
        delivery = order.get('delivery', {})
        address = delivery.get('address', {}) if isinstance(delivery, dict) else {}
        delivery_city = address.get('city')
        delivery_address = address.get('text')

        # Безопасно достаём utm_source
        custom_fields = order.get('customFields', {})
        utm_source = None
        if isinstance(custom_fields, dict):
            utm_source = custom_fields.get('utm_source')

        # Prepare data
        order_data = {
            'crm_id': order_id,
            'first_name': order.get('firstName'),
            'last_name': order.get('lastName'),
            'phone': order.get('phone'),
            'email': order.get('email'),
            'total_sum': order.get('totalSumm', 0),
            'status': order.get('status', 'new'),
            'order_type': order.get('orderType'),
            'order_method': order.get('orderMethod'),
            'ai_analysis': ai_analysis,
            'items': order.get('items', []),
            'delivery_city': delivery_city,
            'delivery_address': delivery_address,
            'utm_source': utm_source
        }

        # Save to Supabase
        if self.supabase.insert_order(order_data):
            # Send notification with full AI analysis
            self.send_new_order_notification(order, ai_analysis)
            return True
        else:
            print(f"❌ Failed to save order {order_id}")
            return False

    def send_new_order_notification(self, order, ai_analysis):
        """Отправляет уведомление о новом заказе с полным AI анализом"""

        # Эмодзи для приоритета
        priority_emoji = {
            'обычный': '📦',
            'высокий': '⚡',
            'срочный': '🚨'
        }

        # Эмодзи для категории
        category_emoji = {
            'новый': '🆕',
            'постоянный': '👤',
            'VIP': '⭐'
        }

        # Эмодзи для риска
        risk_emoji = {
            'низкий': '✅',
            'средний': '⚠️',
            'высокий': '🔴'
        }

        emoji = priority_emoji.get(ai_analysis.get('priority', 'обычный'), '📦')
        cat_emoji = category_emoji.get(ai_analysis.get('customer_category', 'новый'), '🆕')
        risk_emoji_char = risk_emoji.get(ai_analysis.get('cancellation_risk', 'средний'), '⚠️')

        total_sum = order.get('totalSumm', 0)
        if total_sum is None:
            total_sum = 0

        # Формируем полное сообщение
        message = f"""
{emoji} <b>НОВЫЙ ЗАКАЗ!</b>

🆔 Заказ: #{order.get('id')}
👤 Клиент: {order.get('firstName', '')} {order.get('lastName', '')}
📱 Телефон: {order.get('phone', 'не указан')}
💰 Сумма: {int(total_sum):,} ₸

━━━━━━━━━━━━━━━━━━━━
🤖 <b>AI АНАЛИЗ</b>
━━━━━━━━━━━━━━━━━━━━

{cat_emoji} <b>Категория:</b> {ai_analysis.get('customer_category', 'новый')}
{risk_emoji_char} <b>Риск отмены:</b> {ai_analysis.get('cancellation_risk', 'средний')}
⚡ <b>Приоритет:</b> {ai_analysis.get('priority', 'обычный')}
😊 <b>Настроение клиента:</b> {ai_analysis.get('customer_mood', 'нейтральный')}

━━━━━━━━━━━━━━━━━━━━
💡 <b>АНАЛИЗ</b>
━━━━━━━━━━━━━━━━━━━━

📝 {ai_analysis.get('analysis_summary', 'Анализ выполнен')}

━━━━━━━━━━━━━━━━━━━━
🎯 <b>ЧТО ДЕЛАТЬ ПРОДАВЦУ</b>
━━━━━━━━━━━━━━━━━━━━

{ai_analysis.get('seller_action', 'Подтвердите заказ')}

━━━━━━━━━━━━━━━━━━━━
💝 <b>ПЕРСОНАЛЬНОЕ ПРЕДЛОЖЕНИЕ</b>
━━━━━━━━━━━━━━━━━━━━

{ai_analysis.get('personal_offer', 'Спасибо за заказ!')}

━━━━━━━━━━━━━━━━━━━━
📦 <b>ЧТО ЕЩЕ ПРЕДЛОЖИТЬ</b>
━━━━━━━━━━━━━━━━━━━━

{', '.join(ai_analysis.get('upsell_recommendations', ['Аксессуары', 'Гарантия']))}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""

        self.telegram.send_message(message)

    def polling_cycle(self):
        """Один цикл проверки"""
        print(f"\n🔄 {datetime.now().strftime('%H:%M:%S')} - Checking for new orders...")

        try:
            # Получаем последний ID из нашей базы
            last_order_id = self.get_max_order_id_from_ai_orders()
            print(f"   📊 Last processed order ID: {last_order_id}")

            # Получаем новые заказы из RetailCRM
            new_orders = self.get_new_orders_from_crm(last_order_id)

            if not new_orders:
                print("   📭 No new orders found")
                return

            print(f"   🆕 Found {len(new_orders)} new orders")

            # Обрабатываем каждый новый заказ
            processed = 0
            for order in new_orders:
                if self.process_new_order(order):
                    processed += 1

            if processed > 0:
                print(f"   ✅ Successfully processed {processed} orders")

        except Exception as e:
            print(f"   ❌ Polling error: {e}")
            self.telegram.send_message(f"❌ Ошибка мониторинга: {e}")

    def start_monitoring(self, interval_minutes=3):
        """Запуск мониторинга"""
        print(f"🚀 Starting smart polling...")
        print(f"⏰ Check interval: {interval_minutes} minutes")
        print(f"🔄 Press Ctrl+C to stop")

        # Отправляем уведомление о запуске
        self.telegram.send_message(f"""
🚀 <b>Smart Polling запущен</b>

⏰ Интервал: {interval_minutes} минут
📊 Последний заказ в системе: {self.get_max_order_id_from_ai_orders()}
🤖 AI анализ включен

Система готова к работе!
""")

        try:
            # Первая проверка сразу
            self.polling_cycle()

            # Затем проверяем каждые N минут
            while True:
                time.sleep(interval_minutes * 60)
                self.polling_cycle()

        except KeyboardInterrupt:
            print("\n🛑 Smart polling stopped by user")
            self.telegram.send_message("🛑 Smart Polling остановлен")


def main():
    print("🤖 AI Retail Automation - Smart Polling")
    print("=" * 50)

    polling = SmartPolling()

    # Запускаем мониторинг (проверка каждые 3 минуты)
    polling.start_monitoring(interval_minutes=3)


if __name__ == "__main__":
    main()