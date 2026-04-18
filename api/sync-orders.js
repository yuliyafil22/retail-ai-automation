// sync-orders.js НОВЫЙ ФАЙЛ: Vercel Serverless функция для синхронизации заказов
// Аналог твоего smart_polling.py, но для Vercel

import { createClient } from '@supabase/supabase-js'

// Environment variables
const RETAILCRM_URL = process.env.RETAILCRM_URL
const RETAILCRM_APIKEY = process.env.RETAILCRM_APIKEY
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID

// Initialize Supabase (аналог твоего SupabaseClient)
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// AI Analysis (аналог твоего OrderAnalyzer)
function analyzeOrder(order) {
  const totalSum = order.totalSumm || 0

  let category, priority, risk

  if (totalSum > 100000) {
    category = "VIP"
    priority = "высокий"
    risk = "низкий"
  } else if (totalSum > 50000) {
    category = "постоянный"
    priority = "обычный"
    risk = "низкий"
  } else {
    category = "новый"
    priority = "обычный"
    risk = "средний"
  }

  return {
    customer_category: category,
    cancellation_risk: risk,
    priority: priority,
    upsell_recommendations: ["Аксессуары", "Гарантия"],
    personal_offer: "Спасибо за заказ!",
    analysis_summary: `Заказ на ${totalSum.toLocaleString()} ₸ - ${category} клиент`
  }
}

// Telegram notification (аналог твоего TelegramClient)
async function sendTelegramMessage(text) {
  try {
    const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text: text,
        parse_mode: 'HTML'
      })
    })
    return response.ok
  } catch (error) {
    console.error('Telegram error:', error)
    return false
  }
}

// Get max order ID (аналог твоего get_max_order_id_from_ai_orders)
async function getMaxOrderId() {
  try {
    const { data, error } = await supabase
      .from('ai_orders')
      .select('crm_id')
      .lt('crm_id', 888888) // Исключаем тестовые заказы
      .order('crm_id', { ascending: false })
      .limit(1)

    if (error) throw error
    return data.length > 0 ? data[0].crm_id : 0
  } catch (error) {
    console.error('Error getting max order ID:', error)
    return 0
  }
}

// Get new orders from RetailCRM (аналог твоего get_new_orders_from_crm)
async function getNewOrdersFromCRM(lastOrderId) {
  try {
    const response = await fetch(`${RETAILCRM_URL}/api/v5/orders?apiKey=${RETAILCRM_APIKEY}&limit=100&page=1`)

    if (!response.ok) {
      throw new Error(`RetailCRM API error: ${response.status}`)
    }

    const data = await response.json()
    const orders = data.orders || []

    // Filter only new orders
    return orders.filter(order => order.id > lastOrderId)
  } catch (error) {
    console.error('Error getting orders from CRM:', error)
    return []
  }
}

// Process new order (аналог твоего process_new_order)
async function processNewOrder(order) {
  try {
    const aiAnalysis = analyzeOrder(order)

    const orderData = {
      crm_id: order.id,
      first_name: order.firstName,
      last_name: order.lastName,
      phone: order.phone,
      email: order.email,
      total_sum: order.totalSumm || 0,
      status: order.status || 'new',
      order_type: order.orderType,
      order_method: order.orderMethod,
      ai_analysis: aiAnalysis,
      items: order.items || [],
      delivery_city: order.delivery?.address?.city,
      delivery_address: order.delivery?.address?.text,
      utm_source: order.customFields?.utm_source,
      synced_at: new Date().toISOString()
    }

    // Save to Supabase (аналог твоего supabase.insert_order)
    const { error } = await supabase
      .from('ai_orders')
      .insert([orderData])

    if (error) throw error

    // Send Telegram notification (аналог твоего send_new_order_notification)
    const priorityEmoji = { 'обычный': '📦', 'высокий': '⚡', 'срочный': '🚨' }
    const categoryEmoji = { 'новый': '🆕', 'постоянный': '👤', 'VIP': '⭐' }

    const emoji = priorityEmoji[aiAnalysis.priority] || '📦'
    const catEmoji = categoryEmoji[aiAnalysis.customer_category] || '🆕'

    const message = `
${emoji} <b>НОВЫЙ ЗАКАЗ!</b>

🆔 Заказ: #${order.id}
👤 Клиент: ${order.firstName || ''} ${order.lastName || ''}
📱 Телефон: ${order.phone || 'не указан'}
💰 Сумма: ${(order.totalSumm || 0).toLocaleString()} ₸

🤖 <b>AI Анализ:</b>
${catEmoji} Категория: ${aiAnalysis.customer_category}
⚡ Приоритет: ${aiAnalysis.priority}

💡 ${aiAnalysis.analysis_summary}

⏰ ${new Date().toLocaleTimeString()}
🌐 Processed by Vercel
`

    await sendTelegramMessage(message)

    return true
  } catch (error) {
    console.error('Error processing order:', error)
    return false
  }
}

// Main handler (аналог твоего polling_cycle)
export default async function handler(req, res) {
  const startTime = new Date()
  console.log('🔄 Vercel sync started at:', startTime.toISOString())

  try {
    // Get last processed order ID
    const lastOrderId = await getMaxOrderId()
    console.log('📊 Last processed order ID:', lastOrderId)

    // Get new orders from RetailCRM
    const newOrders = await getNewOrdersFromCRM(lastOrderId)
    console.log('🆕 Found new orders:', newOrders.length)

    if (newOrders.length === 0) {
      return res.status(200).json({
        success: true,
        message: 'No new orders found',
        lastOrderId,
        timestamp: startTime.toISOString(),
        executionTime: Date.now() - startTime.getTime()
      })
    }

    // Process each new order
    let processed = 0
    const results = []

    for (const order of newOrders) {
      const success = await processNewOrder(order)
      if (success) {
        processed++
        results.push({ orderId: order.id, status: 'success' })
      } else {
        results.push({ orderId: order.id, status: 'error' })
      }
    }

    // Send summary notification
    if (processed > 0) {
      await sendTelegramMessage(`
📊 <b>Vercel Sync Summary</b>

✅ Обработано: ${processed} заказов
📦 Всего проверено: ${newOrders.length}
⏰ Время: ${new Date().toLocaleTimeString()}
🌐 Powered by Vercel Cron
⚡ Время выполнения: ${Date.now() - startTime.getTime()}ms
`)
    }

    return res.status(200).json({
      success: true,
      message: `Processed ${processed} new orders`,
      stats: {
        newOrders: newOrders.length,
        processed,
        failed: newOrders.length - processed,
        lastOrderId,
        executionTime: Date.now() - startTime.getTime()
      },
      results,
      timestamp: startTime.toISOString()
    })

  } catch (error) {
    console.error('❌ Vercel sync error:', error)

    // Send error notification
    await sendTelegramMessage(`
❌ <b>Vercel Sync Error</b>

Ошибка: ${error.message}
⏰ Время: ${new Date().toLocaleTimeString()}
🌐 Vercel Function
`)

    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: startTime.toISOString(),
      executionTime: Date.now() - startTime.getTime()
    })
  }
}

