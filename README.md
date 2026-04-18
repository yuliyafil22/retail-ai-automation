# 🤖 Retail AI Automation Platform

Интеллектуальная система автоматизации для интернет-магазинов с AI-ассистентом

---

## 🎯 Возможности

### 🤖 AI-Ассистент (OpenAI GPT-4o-mini)
- Анализ заказов в реальном времени
- Определение категории клиента (VIP/постоянный/новый)
- Прогнозирование риска отмены заказа
- Приоритизация заказов для продавца
- Персональные рекомендации товаров (upsell)
- Анализ настроения клиента по комментарию

### 📱 Telegram Bot
- Уведомления о новых заказах с AI-анализом
- Поиск заказа по номеру (`/find 12345`)
- Статистика за сегодня (`/stats`)
- Последние заказы (`/orders`)
- Постоянное меню с кнопками

### 🔄 Автоматизация
- Polling интеграция с RetailCRM (раз в 3 минуты)
- Автоматический AI анализ каждого заказа
- Real-time дашборд с KPI - https://retail-ai-automation.vercel.app/
- Хранение истории заказов в Supabase

---

## 🛠 Технологический стек

| Компонент     | Технология            |
|---------------|-----------------------|
| **AI Engine** | OpenAI GPT-4o-mini    |
| **Database**  | Supabase (PostgreSQL) |
| **CRM**       | RetailCRM API         |
| **Messaging** | Telegram Bot API      |
| **Frontend**  | HTML/CSS/JS           |
| **Hosting**   | Vercel + локальный polling |
| **Language**  | Python 3.14+          |

---

## 🧠 Схема логики работы

<img width="975" height="104" alt="image" src="https://github.com/user-attachments/assets/5c26bd0b-3248-49ad-bced-a39d0795cd83" />

---

## 🚀 Быстрый старт

### 1. Клонирование
```bash
git clone https://github.com/your-username/retail-ai-automation.git
cd retail-ai-automation
2. Установка зависимостей
bash
pip install -r requirements.txt
3. Настройка переменных окружения
bash
cp .env.example .env
# Отредактируй .env, добавь ключи
4. Запуск
bash
# Терминал 1: Telegram бот
python run_bot.py

# Терминал 2: Polling (проверка новых заказов)
python smart_polling.py
🤖 Telegram Bot команды
Команда	Описание
/start	Главное меню с кнопками
/stats	Статистика за сегодня
/orders	Последние 10 заказов
/find 12345	Поиск заказа по номеру
Постоянное меню внизу экрана:
🏠 Главное меню | 📊 Статистика | 📋 Заказы | 🔍 Поиск заказа | ❓ Помощь


🎯 Применение
Идеально подходит для:

🛍️ E-commerce автоматизации — AI анализ каждого заказа

📞 Клиентского сервиса — быстрая реакция на проблемы

⚡ Операционной оптимизации — приоритизация заказов

🧠 AI-driven продаж — персонализированные предложения

📝 Лицензия
MIT

👤 Автор
Yuliya Filatova  — ссылка на [LinkedIn/GitHub]](https://www.linkedin.com/in/yuliyafilatova/

⭐ Если проект полезен
Поставь звезду ⭐ и поделись с коллегами!
