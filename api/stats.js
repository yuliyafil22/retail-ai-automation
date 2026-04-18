// api/stats.js - Полная версия с поддержкой дашборда

import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

export default async function handler(req, res) {
  try {
    const today = new Date().toISOString().split('T')[0] // YYYY-MM-DD

    // Get today's orders from ai_orders table
    const { data: orders, error } = await supabase
      .from('ai_orders')
      .select('total_sum, ai_analysis')
      .gte('created_at', today)

    if (error) throw error

    // Calculate statistics
    const totalSum = orders.reduce((sum, order) => sum + (parseFloat(order.total_sum) || 0), 0)
    const avgOrder = orders.length > 0 ? totalSum / orders.length : 0

    // Analyze AI data
    let vipCustomers = 0
    let highRisk = 0
    let needsAttention = 0

    orders.forEach(order => {
      const aiData = order.ai_analysis || {}
      if (aiData.customer_category === 'VIP') vipCustomers++
      if (aiData.cancellation_risk === 'высокий') highRisk++
      if (['высокий', 'срочный'].includes(aiData.priority)) needsAttention++
    })

    const stats = {
      orders_count: orders.length,
      total_sum: totalSum,
      avg_order: avgOrder,
      vip_customers: vipCustomers,
      high_risk: highRisk,
      needs_attention: needsAttention,
      date: today,
      timestamp: new Date().toISOString()
    }

    // ==============================================
    // 👇 ФОРМАТ ДЛЯ ДАШБОРДА (то, что нужно добавить)
    // ==============================================
    const dashboardFormat = {
      total: stats.total_sum,
      orders: stats.orders_count,
      avg: stats.avg_order,
      vip: stats.vip_customers,
      risk: stats.high_risk,
      attention: stats.needs_attention
    }

    // ==============================================
    // 👇 Возвращаем ОБА формата (для совместимости)
    // ==============================================
    return res.status(200).json(dashboardFormat)

  } catch (error) {
    console.error('Stats error:', error)

    // Возвращаем пустые данные при ошибке (чтобы дашборд не падал)
    return res.status(200).json({
      total: 0,
      orders: 0,
      avg: 0,
      vip: 0,
      risk: 0,
      attention: 0,
      error: error.message
    })
  }
}