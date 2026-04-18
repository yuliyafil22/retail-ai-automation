# bot/handlers.py - ИСПРАВЛЕННАЯ ВЕРСИЯ (без ошибок HTML)

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from src.config.settings import settings
from src.integrations.supabase_client import SupabaseClient
from datetime import datetime

bot = telebot.TeleBot(settings.TELEGRAM_TOKEN)
supabase = SupabaseClient()


# ==================== ПОСТОЯННОЕ МЕНЮ (ВСЕГДА ВНИЗУ) ====================
def get_main_keyboard():
    """Создает постоянную клавиатуру внизу экрана"""
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        row_width=2
    )

    buttons = [
        KeyboardButton("🏠 Главное меню"),
        KeyboardButton("📊 Статистика"),
        KeyboardButton("📋 Заказы"),
        KeyboardButton("🔍 Поиск заказа"),
        KeyboardButton("❓ Помощь")
    ]

    keyboard.add(*buttons)
    return keyboard


# ==================== КОМАНДА /start ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "🤖 <b>AI Retail Assistant</b>\n\n"
        "Я помогаю продавцам отслеживать заказы и анализировать продажи.\n\n"
        "📌 <b>Что я умею:</b>\n"
        "• 📊 Статистика за сегодня\n"
        "• 📋 Последние заказы\n"
        "• 🔍 Поиск заказа по номеру\n"
        "• ⚡ Уведомления о новых заказах\n\n"
        "👇 <b>Используйте кнопки внизу экрана</b> 👇",
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )


# ==================== КОМАНДА /help (ИСПРАВЛЕНА - без сложных тегов) ====================
@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
❓ ПОМОЩЬ ПО КОМАНДАМ

━━━━━━━━━━━━━━━━━━━━
📌 Кнопки внизу экрана:
━━━━━━━━━━━━━━━━━━━━

🏠 Главное меню
   → Показать приветствие

📊 Статистика
   → Статистика за сегодня:
   • Количество заказов
   • Выручка
   • Средний чек
   • VIP клиенты

📋 Заказы
   → Последние 10 заказов

🔍 Поиск заказа
   → Найти заказ по номеру
   → Введите номер после нажатия

❓ Помощь
   → Показать эту справку

━━━━━━━━━━━━━━━━━━━━
📌 Текстовые команды:
━━━━━━━━━━━━━━━━━━━━

/start - Главное меню
/help  - Эта справка
/stats - Статистика
/orders - Последние заказы
/find 12345 - Поиск заказа

━━━━━━━━━━━━━━━━━━━━
🤖 AI Аналитика:
━━━━━━━━━━━━━━━━━━━━

⭐ VIP клиенты → сумма > 100 000 ₸
⚠️ Высокий риск → сумма < 50 000 ₸
🔥 Требуют внимания → VIP заказы

💡 Бот автоматически уведомляет о новых заказах
"""
    bot.send_message(message.chat.id, text, parse_mode=None, reply_markup=get_main_keyboard())


# ==================== ОБРАБОТЧИКИ КНОПОК ПОСТОЯННОГО МЕНЮ ====================
@bot.message_handler(func=lambda message: message.text == "🏠 Главное меню")
def main_menu_button(message):
    start_command(message)


@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def stats_button(message):
    show_stats_message(message.chat.id)


@bot.message_handler(func=lambda message: message.text == "📋 Заказы")
def orders_button(message):
    show_orders(message.chat.id)


@bot.message_handler(func=lambda message: message.text == "🔍 Поиск заказа")
def search_button(message):
    msg = bot.send_message(
        message.chat.id,
        "🔍 <b>Поиск заказа</b>\n\n"
        "Введите номер заказа цифрами.\n"
        "Пример: 12345\n\n"
        "✏️ Напишите номер в чат:",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_order_number)


@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def help_button(message):
    help_command(message)


# ==================== ОБРАБОТЧИК ПОИСКА ПО НОМЕРУ ====================
def process_order_number(message):
    """Обрабатывает введенный номер заказа"""
    try:
        order_id = int(message.text.strip())
        order = supabase.get_order_by_crm_id(order_id)

        if order:
            ai_data = order.get('ai_analysis', {})

            vip_mark = "⭐ VIP" if ai_data.get('customer_category') == 'VIP' else "🆕 Обычный"
            risk_mark = "⚠️ Высокий риск" if ai_data.get('cancellation_risk') == 'высокий' else "✅ Риск низкий"

            total_sum = order.get('total_sum', 0)
            if total_sum is None:
                total_sum = 0

            text = f"""
🔍 <b>Заказ #{order['crm_id']}</b>

💰 Сумма: {int(total_sum):,} ₸
👤 Клиент: {order.get('first_name', '-')} {order.get('last_name', '')}
📱 Телефон: {order.get('phone', '-')}
📊 Статус: {order.get('status', 'новый')}

🤖 <b>AI Анализ:</b>
{vip_mark}
{risk_mark}

📅 Создан: {order.get('created_at', '-')[:10] if order.get('created_at') else '-'}
"""
        else:
            text = f"❌ Заказ #{order_id} не найден\n\nПроверьте номер и попробуйте снова."

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=get_main_keyboard())

    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Некорректный номер. Введите только цифры.\n\nПример: 12345",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Ошибка поиска: {str(e)}",
            reply_markup=get_main_keyboard()
        )


# ==================== КОМАНДА /stats ====================
@bot.message_handler(commands=['stats'])
def stats_command(message):
    show_stats_message(message.chat.id)


# ==================== КОМАНДА /orders ====================
@bot.message_handler(commands=['orders'])
def orders_command(message):
    show_orders(message.chat.id)


# ==================== КОМАНДА /find ====================
@bot.message_handler(commands=['find'])
def find_order_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(
                message,
                "❌ Укажите номер заказа.\n\nПример: /find 12345",
                parse_mode=None
            )
            return

        order_id = int(parts[1])
        order = supabase.get_order_by_crm_id(order_id)

        if order:
            ai_data = order.get('ai_analysis', {})

            vip_mark = "⭐ VIP" if ai_data.get('customer_category') == 'VIP' else "🆕 Обычный"
            risk_mark = "⚠️ Высокий риск" if ai_data.get('cancellation_risk') == 'высокий' else "✅ Риск низкий"

            total_sum = order.get('total_sum', 0)
            if total_sum is None:
                total_sum = 0

            text = f"""
🔍 Заказ #{order['crm_id']}

💰 Сумма: {int(total_sum):,} ₸
👤 Клиент: {order.get('first_name', '-')} {order.get('last_name', '')}
📱 Телефон: {order.get('phone', '-')}
📊 Статус: {order.get('status', 'новый')}

🤖 AI Анализ:
{vip_mark}
{risk_mark}

📅 Создан: {order.get('created_at', '-')[:10] if order.get('created_at') else '-'}
"""
        else:
            text = f"❌ Заказ #{order_id} не найден"

        bot.reply_to(message, text, parse_mode=None)

    except ValueError:
        bot.reply_to(message, "❌ Некорректный номер заказа.\nПример: /find 12345")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка поиска: {str(e)}")


# ==================== ОБРАБОТЧИКИ INLINE КНОПОК ====================
@bot.callback_query_handler(func=lambda call: call.data == "stats")
def handle_stats_callback(call):
    show_stats_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "orders")
def handle_orders_callback(call):
    show_orders(call.message.chat.id)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "search")
def handle_search_callback(call):
    msg = bot.send_message(
        call.message.chat.id,
        "🔍 Поиск заказа\n\nВведите номер заказа:",
        parse_mode=None
    )
    bot.register_next_step_handler(msg, process_order_number)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "help")
def handle_help_callback(call):
    help_command(call.message)
    bot.answer_callback_query(call.id)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def show_stats_message(chat_id, message_id=None):
    """Показать статистику"""
    stats = supabase.get_today_stats()

    if isinstance(stats, dict) and 'error' in stats:
        text = f"❌ Ошибка получения статистики: {stats['error']}"
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=get_main_keyboard())
        else:
            bot.send_message(chat_id, text, reply_markup=get_main_keyboard())
        return

    total_sum = stats.get('total_sum', 0)
    avg_order = stats.get('avg_order', 0)

    if total_sum is None:
        total_sum = 0
    if avg_order is None:
        avg_order = 0

    text = f"""
📊 Статистика за сегодня ({datetime.now().strftime('%d.%m.%Y')})

━━━━━━━━━━━━━━━━━━━━
📦 Заказов: {stats.get('orders_count', 0)}
💰 Выручка: {int(total_sum):,} ₸
📈 Средний чек: {int(avg_order):,} ₸
━━━━━━━━━━━━━━━━━━━━

🤖 AI Аналитика:
⭐ VIP клиентов: {stats.get('vip_customers', 0)}
⚠️ Высокий риск отмены: {stats.get('high_risk', 0)}
🔥 Требуют внимания: {stats.get('needs_attention', 0)}

💡 VIP = сумма заказа > 100 000 ₸
"""

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode=None)
    else:
        bot.send_message(chat_id, text, parse_mode=None, reply_markup=get_main_keyboard())


def show_orders(chat_id):
    """Показать последние заказы"""
    try:
        orders = supabase.get_recent_orders(limit=10)

        if not orders:
            bot.send_message(chat_id, "📭 Нет заказов за последнее время", parse_mode=None,
                             reply_markup=get_main_keyboard())
            return

        text = "📋 Последние заказы:\n\n"

        for order in orders[:10]:
            status_emoji = {
                'new': '🆕',
                'paid': '✅',
                'delivered': '🚚',
                'cancelled': '❌'
            }.get(order.get('status', 'new'), '📦')

            vip_mark = " ⭐" if order.get('is_vip') else ""

            total_sum = order.get('total_sum', 0)
            if total_sum is None:
                total_sum = 0

            text += f"{status_emoji} #{order['crm_id']}{vip_mark}\n"
            text += f"   💰 {int(total_sum):,} ₸\n"
            text += f"   👤 {order.get('first_name', '-')}\n"
            text += f"   ━━━━━━━━━━━━━━━━━━━━\n"

        text += "\n🔍 Для поиска нажмите кнопку 🔍 Поиск заказа внизу"
        bot.send_message(chat_id, text, parse_mode=None, reply_markup=get_main_keyboard())

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка загрузки заказов: {str(e)}", reply_markup=get_main_keyboard())


# ==================== ЗАПУСК БОТА ====================
def run_bot():
    """Запуск бота в режиме polling"""
    print("=" * 50)
    print("🤖 ЗАПУСК TELEGRAM БОТА")
    print("=" * 50)

    try:
        bot_info = bot.get_me()
        print(f"✅ Бот подключен: @{bot_info.username}")
        print(f"📱 ID бота: {bot_info.id}")
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return

    print(f"🔄 Режим polling запущен...")
    print("=" * 50)
    print("")
    print("📌 Доступные команды:")
    print("   /start  - Главное меню")
    print("   /help   - Помощь")
    print("   /stats  - Статистика")
    print("   /orders - Заказы")
    print("   /find   - Поиск заказа")
    print("")
    print("⏹️  Нажми Ctrl+C для остановки")
    print("=" * 50)
    print("")

    # Отправляем уведомление админу о запуске
    if settings.TELEGRAM_CHAT_ID:
        try:
            bot.send_message(
                settings.TELEGRAM_CHAT_ID,
                "✅ AI Retail Assistant запущен!\n\n"
                "Бот готов к работе.\n"
                "Нажмите /start для начала.",
                parse_mode=None,
                reply_markup=get_main_keyboard()
            )
            print("📨 Уведомление администратору отправлено")
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление: {e}")

    # Запускаем бота
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Ошибка polling: {e}")
        raise


# ==================== ТОЧКА ВХОДА ====================
if __name__ == "__main__":
    run_bot()