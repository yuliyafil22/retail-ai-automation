# src/integrations/supabase_client.py

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Добавляем путь к корню проекта
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # src/integrations -> src -> корень
sys.path.insert(0, str(project_root))

# Теперь импорт работает
from src.config.settings import settings


class SupabaseClient:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.table_name = "ai_orders"

        if self.url and self.key:
            self.headers = {
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
        else:
            self.headers = None
            print("❌ Supabase не настроен (проверьте .env)")

    def insert_order(self, order_data: Dict) -> bool:
        """Insert order into ai_orders table"""
        if not self.headers:
            print("Supabase not configured")
            return False

        try:
            url = f"{self.url}/rest/v1/{self.table_name}"

            # Prepare data for new table
            prepared_data = {
                'crm_id': order_data.get('crm_id'),
                'first_name': order_data.get('first_name'),
                'last_name': order_data.get('last_name'),
                'phone': order_data.get('phone'),
                'email': order_data.get('email'),
                'total_sum': order_data.get('total_sum'),
                'status': order_data.get('status', 'new'),
                'order_type': order_data.get('order_type'),
                'order_method': order_data.get('order_method'),
                'ai_analysis': order_data.get('ai_analysis'),
                'items': order_data.get('items'),
                'delivery_city': order_data.get('delivery_city'),
                'delivery_address': order_data.get('delivery_address'),
                'utm_source': order_data.get('utm_source'),
                'utm_medium': order_data.get('utm_medium'),
                'utm_campaign': order_data.get('utm_campaign'),
                'synced_at': datetime.now().isoformat()
            }

            # Remove None values
            prepared_data = {k: v for k, v in prepared_data.items() if v is not None}

            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(prepared_data)
            )

            if response.status_code in (200, 201):
                print(f"✅ Order {order_data.get('crm_id')} saved to ai_orders")
                return True
            else:
                print(f"❌ Supabase error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Supabase error: {e}")
            return False

    def get_order_by_crm_id(self, crm_id: int) -> Optional[Dict]:
        """Get order by CRM ID"""
        if not self.headers:
            return None

        try:
            url = f"{self.url}/rest/v1/{self.table_name}"
            params = {'crm_id': f'eq.{crm_id}'}

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                orders = response.json()
                return orders[0] if orders else None
            else:
                print(f"Error getting order: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error getting order: {e}")
            return None

    def get_today_stats(self) -> Dict:
        """Get today statistics"""
        if not self.headers:
            return {"error": "Supabase not configured"}

        try:
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"{self.url}/rest/v1/{self.table_name}"
            params = {
                'created_at': f'gte.{today}',
                'select': 'total_sum, ai_analysis'
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                orders = response.json()
                total_sum = sum(float(order.get('total_sum', 0)) for order in orders)
                avg_order = total_sum / len(orders) if orders else 0

                # Analyze AI data
                vip_customers = 0
                high_risk = 0
                needs_attention = 0

                for order in orders:
                    ai_data = order.get('ai_analysis', {})
                    if ai_data.get('customer_category') == 'VIP':
                        vip_customers += 1
                    if ai_data.get('cancellation_risk') == 'высокий':
                        high_risk += 1
                    if ai_data.get('priority') in ['высокий', 'срочный']:
                        needs_attention += 1

                return {
                    'orders_count': len(orders),
                    'total_sum': total_sum,
                    'avg_order': avg_order,
                    'vip_customers': vip_customers,
                    'high_risk': high_risk,
                    'needs_attention': needs_attention
                }
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    def get_recent_orders(self, limit: int = 10) -> List[Dict]:
        """Get recent orders"""
        if not self.headers:
            return []

        try:
            url = f"{self.url}/rest/v1/{self.table_name}"
            params = {
                'select': 'crm_id,total_sum,first_name,status,created_at,ai_analysis',
                'order': 'created_at.desc',
                'limit': limit
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                orders = response.json()
                # Добавляем is_vip для удобства
                for order in orders:
                    ai_data = order.get('ai_analysis', {})
                    order['is_vip'] = ai_data.get('customer_category') == 'VIP'
                return orders
            else:
                return []
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

    def check_table_structure(self) -> Dict:
        """Check new table structure"""
        if not self.headers:
            return {"error": "Supabase not configured"}

        try:
            url = f"{self.url}/rest/v1/{self.table_name}?limit=1"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return {
                    "status": "ok",
                    "table": self.table_name,
                    "sample_data": response.json()
                }
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}