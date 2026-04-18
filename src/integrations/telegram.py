#integrations/telegram.py

import requests
from typing import Optional


class TelegramClient:
    def __init__(self):
        # Импортируем settings здесь, чтобы избежать циклических импортов
        from src.config.settings import settings

        self.token = settings.TELEGRAM_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        if self.token:
            self.base_url = f"https://api.telegram.org/bot{self.token}"
        else:
            self.base_url = None

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Отправка простого сообщения"""
        if not self.token or not self.chat_id:
            print("❌ Telegram не настроен (нет токена или chat_id)")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("✅ Сообщение отправлено в Telegram")
                return True
            else:
                print(f"❌ Ошибка Telegram: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False

    def send_smart_message(self, text: str, order_id: Optional[int] = None) -> bool:
        """Отправка умного сообщения с кнопками"""
        # Пока просто отправляем текст, кнопки добавим позже
        return self.send_message(text)