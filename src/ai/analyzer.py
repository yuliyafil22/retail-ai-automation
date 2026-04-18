# ai/analyzer.py - OpenAI основной, DeepSeek и Gemini как резерв

from typing import Dict, Optional
from src.config.settings import settings
import json
import re
import requests
from openai import OpenAI

print("🔍 [DIAGNOSTIC] Начинаем импорт модулей...")

# OpenAI
try:
    OPENAI_AVAILABLE = True
    print("✅ [DIAGNOSTIC] OpenAI библиотека готова")
except ImportError as e:
    OPENAI_AVAILABLE = False
    print(f"❌ [DIAGNOSTIC] OpenAI НЕ доступен: {e}")

# Gemini (резерв)
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
    print("✅ [DIAGNOSTIC] google.generativeai импортирован")
except ImportError:
    GEMINI_AVAILABLE = False
    print("❌ [DIAGNOSTIC] google.generativeai НЕ импортирован")


class OrderAnalyzer:
    def __init__(self):
        print("🔍 [DIAGNOSTIC] Инициализация OrderAnalyzer...")

        # API ключи
        self.openai_key = settings.OPENAI_API_KEY
        self.deepseek_key = settings.DEEPSEEK_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

        print(f"🔍 [DIAGNOSTIC] openai_key = {'✅ есть' if self.openai_key else '❌ нет'}")
        print(f"🔍 [DIAGNOSTIC] deepseek_key = {'✅ есть' if self.deepseek_key else '❌ нет'}")
        print(f"🔍 [DIAGNOSTIC] gemini_key = {'✅ есть' if self.gemini_key else '❌ нет'}")

        self.current_provider = None
        self.use_real_ai = False

        # Список моделей Gemini для попытки
        self.gemini_models = [
            'gemini-2.0-flash',
            'gemini-1.5-flash',
            'gemini-pro'
        ]
        self.gemini_model = None

        # 1. Пробуем OpenAI (основной)
        print("🔍 [DIAGNOSTIC] Проверяем OpenAI...")
        if self.openai_key:
            if self._check_openai():
                self.current_provider = 'openai'
                self.use_real_ai = True
                print("✅ OpenAI API доступен (основной)")

        # 2. Если OpenAI не работает, пробуем DeepSeek
        if not self.use_real_ai and self.deepseek_key:
            print("🔍 [DIAGNOSTIC] Проверяем DeepSeek...")
            if self._check_deepseek():
                self.current_provider = 'deepseek'
                self.use_real_ai = True
                print("✅ DeepSeek API доступен (резерв)")

        # 3. Если DeepSeek не работает, пробуем Gemini
        if not self.use_real_ai and self.gemini_key and GEMINI_AVAILABLE:
            print("🔍 [DIAGNOSTIC] Проверяем Gemini...")
            if self._check_gemini():
                self.current_provider = 'gemini'
                self.use_real_ai = True
                print(f"✅ Gemini API доступен (резерв, модель: {self.gemini_model})")

        if not self.use_real_ai:
            print("⚠️ Все AI сервисы недоступны, использую fallback-анализ")

    def _check_openai(self) -> bool:
        """Проверяет доступность OpenAI API"""
        try:
            client = OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            print("✅ [DIAGNOSTIC] OpenAI тест успешен")
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [DIAGNOSTIC] OpenAI ошибка: {error_msg[:100]}")
            if "insufficient_quota" in error_msg:
                print("⚠️ OpenAI: Недостаточно средств на счету (нужно пополнить баланс)")
            return False

    def _check_deepseek(self) -> bool:
        """Проверяет доступность DeepSeek API"""
        try:
            test_payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5
            }
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_key}",
                    "Content-Type": "application/json"
                },
                json=test_payload,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ [DIAGNOSTIC] DeepSeek тест успешен")
                return True
            elif response.status_code == 402:
                print("⚠️ DeepSeek: Недостаточно средств на счету")
                return False
            else:
                print(f"⚠️ DeepSeek: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ DeepSeek ошибка: {e}")
            return False

    def _check_gemini(self) -> bool:
        """Проверяет доступность Gemini API"""
        for model_name in self.gemini_models:
            try:
                genai.configure(api_key=self.gemini_key)
                test_model = genai.GenerativeModel(model_name)
                response = test_model.generate_content("Test")
                if response:
                    self.gemini_model = model_name
                    print(f"✅ [DIAGNOSTIC] Gemini модель {model_name} работает!")
                    return True
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"⚠️ Gemini {model_name}: превышен лимит")
                elif "404" in error_msg:
                    print(f"⚠️ Gemini {model_name}: модель не найдена")
        return False

    def analyze_order(self, order: Dict) -> Dict:
        """Анализ заказа с автоматическим переключением между AI"""
        if not self.use_real_ai:
            return self._fallback_analysis(order)

        try:
            if self.current_provider == "openai":
                return self._analyze_with_openai(order)
            elif self.current_provider == "deepseek":
                return self._analyze_with_deepseek(order)
            elif self.current_provider == "gemini":
                return self._analyze_with_gemini(order)
            else:
                return self._fallback_analysis(order)

        except Exception as e:
            error_str = str(e)
            print(f"❌ AI ошибка ({self.current_provider}): {error_str[:100]}")
            return self._fallback_analysis(order)

    def _analyze_with_openai(self, order: Dict) -> Dict:
        """Анализ через OpenAI API"""
        client = OpenAI(api_key=self.openai_key)

        total_sum = order.get('totalSumm', 0) or 0

        items = order.get('items', [])
        items_text = ", ".join([f"{i.get('name', 'Товар')} x{i.get('quantity', 1)}" for i in items[:5]])

        comment = order.get('customerComment', '') or order.get('comment', '')

        prompt = f"""Ты AI-ассистент для интернет-магазина. Проанализируй заказ и верни ТОЛЬКО JSON.

Данные:
- Сумма: {total_sum} ₸
- Товары: {items_text if items_text else 'Нет'}
- Комментарий: {comment if comment else 'Нет'}

Верни JSON:
{{
    "cancellation_risk": "низкий/средний/высокий",
    "priority": "обычный/высокий/срочный",
    "upsell_recommendations": ["товар1", "товар2"],
    "personal_offer": "персональное предложение клиенту",
    "analysis_summary": "краткий вывод для продавца",
    "seller_action": "что конкретно сделать продавцу прямо сейчас",
    "customer_mood": "нейтральный/позитивный/тревожный"
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )

        result_text = response.choices[0].message.content
        ai_result = self._parse_ai_response(result_text)

        # Категория по сумме
        if total_sum > 100000:
            ai_result['customer_category'] = 'VIP'
        elif total_sum > 50000:
            ai_result['customer_category'] = 'постоянный'
        else:
            ai_result['customer_category'] = 'новый'

        return ai_result

    def _analyze_with_deepseek(self, order: Dict) -> Dict:
        """Анализ через DeepSeek API"""
        total_sum = order.get('totalSumm', 0) or 0

        items = order.get('items', [])
        items_text = ", ".join([f"{i.get('name', 'Товар')} x{i.get('quantity', 1)}" for i in items[:5]])

        comment = order.get('customerComment', '') or order.get('comment', '')

        prompt = f"""Ты AI-ассистент для интернет-магазина. Верни ТОЛЬКО JSON.

Данные:
- Сумма: {total_sum} ₸
- Товары: {items_text if items_text else 'Нет'}
- Комментарий: {comment if comment else 'Нет'}

Верни JSON:
{{
    "cancellation_risk": "низкий/средний/высокий",
    "priority": "обычный/высокий/срочный",
    "upsell_recommendations": ["товар1", "товар2"],
    "personal_offer": "предложение",
    "analysis_summary": "вывод",
    "seller_action": "что делать продавцу",
    "customer_mood": "нейтральный/позитивный/тревожный"
}}"""

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"DeepSeek error: {response.status_code}")

        result = response.json()
        result_text = result["choices"][0]["message"]["content"]
        ai_result = self._parse_ai_response(result_text)

        if total_sum > 100000:
            ai_result['customer_category'] = 'VIP'
        elif total_sum > 50000:
            ai_result['customer_category'] = 'постоянный'
        else:
            ai_result['customer_category'] = 'новый'

        return ai_result

    def _analyze_with_gemini(self, order: Dict) -> Dict:
        """Анализ через Gemini API"""
        total_sum = order.get('totalSumm', 0) or 0

        items = order.get('items', [])
        items_text = ", ".join([f"{i.get('name', 'Товар')} x{i.get('quantity', 1)}" for i in items[:5]])

        comment = order.get('customerComment', '') or order.get('comment', '')

        prompt = f"""Верни ТОЛЬКО JSON для заказа:
Сумма: {total_sum} ₸
Товары: {items_text}
Комментарий: {comment}

JSON: {{"cancellation_risk": "...", "priority": "...", "upsell_recommendations": [], "personal_offer": "...", "analysis_summary": "...", "seller_action": "...", "customer_mood": "..."}}"""

        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel(self.gemini_model)
        response = model.generate_content(prompt)

        ai_result = self._parse_ai_response(response.text)

        if total_sum > 100000:
            ai_result['customer_category'] = 'VIP'
        elif total_sum > 50000:
            ai_result['customer_category'] = 'постоянный'
        else:
            ai_result['customer_category'] = 'новый'

        return ai_result

    def _parse_ai_response(self, response_text: str) -> Dict:
        """Парсит JSON из ответа AI"""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "cancellation_risk": result.get("cancellation_risk", "средний"),
                    "priority": result.get("priority", "обычный"),
                    "upsell_recommendations": result.get("upsell_recommendations", []),
                    "personal_offer": result.get("personal_offer", "Спасибо за заказ!"),
                    "analysis_summary": result.get("analysis_summary", "Заказ требует внимания"),
                    "seller_action": result.get("seller_action", "Подтвердите заказ"),
                    "customer_mood": result.get("customer_mood", "нейтральный")
                }
        except Exception as e:
            print(f"❌ Парсинг JSON ошибка: {e}")
        return self._fallback_analysis({})

    def _fallback_analysis(self, order: Dict) -> Dict:
        """Анализ без AI (на основе правил) - ВСЕГДА РАБОТАЕТ"""
        total_sum = order.get('totalSumm', 0) or 0

        comment = order.get('customerComment', '') or order.get('comment', '')
        negative_words = ['проблем', 'брак', 'сломан', 'недовол', 'жалоб', 'плох', 'возврат', 'отмен', 'сомневаюсь',
                          'верну']
        has_negative = any(word in comment.lower() for word in negative_words)

        if total_sum > 100000:
            category = "VIP"
            priority = "высокий"
            risk = "низкий"
            seller_action = "Позвоните клиенту лично, поблагодарите за крупный заказ"
            personal_offer = "Скидка 10% на следующий заказ"
            upsell = ["Премиум доставка", "Расширенная гарантия"]
        elif total_sum > 50000:
            category = "постоянный"
            priority = "обычный"
            risk = "низкий"
            seller_action = "Отправьте подтверждение заказа в Telegram"
            personal_offer = "Бесплатная доставка в подарок"
            upsell = ["Аксессуары", "Страховка"]
        else:
            category = "новый"
            priority = "обычный"
            risk = "средний"
            seller_action = "Подтвердите заказ как можно скорее"
            personal_offer = "Скидка 5% на первый заказ"
            upsell = ["Подарочная упаковка"]

        if has_negative:
            risk = "высокий"
            priority = "срочный"
            seller_action = "СРОЧНО! Свяжитесь с клиентом по телефону"

        return {
            "customer_category": category,
            "cancellation_risk": risk,
            "priority": priority,
            "upsell_recommendations": upsell,
            "personal_offer": personal_offer,
            "analysis_summary": f"Заказ на {total_sum:,} ₸ от {category} клиента",
            "seller_action": seller_action,
            "customer_mood": "тревожный" if risk == "высокий" else "нейтральный"
        }


order_analyzer = OrderAnalyzer()