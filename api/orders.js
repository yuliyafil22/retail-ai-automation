// api/orders.js - Эндпоинт для списка заказов (дашборд + CRM)

import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

export default async function handler(req, res) {
  try {
    // Берем последние 20 заказов из ai_orders
    const { data: orders, error } = await supabase
      .from('ai_orders')
      .select('crm_id, total_sum, first_name, last_name, status, created_at, ai_analysis, phone, email')
      .order('created_at', { ascending: false })
      .limit(20)

    if (error) throw error

    // Форматируем для дашборда
    const formattedOrders = orders.map(order => ({
      crm_id: order.crm_id,
      total_sum: order.total_sum,
      first_name: order.first_name || 'Аноним',
      last_name: order.last_name || '',
      status: order.status || 'новый',
      created_at: order.created_at,
      phone: order.phone || '',
      email: order.email || '',
      // AI метки для дашборда
      is_vip: order.ai_analysis?.customer_category === 'VIP',
      risk: order.ai_analysis?.cancellation_risk || 'низкий',
      priority: order.ai_analysis?.priority || 'обычный'
    }))

    return res.status(200).json(formattedOrders)

  } catch (error) {
    console.error('Orders API error:', error)
    return res.status(200).json([]) // Возвращаем пустой массив при ошибке
  }
}

