// test.js НОВЫЙ ФАЙЛ: Простой тест API
export default async function handler(req, res) {
  const timestamp = new Date().toISOString()

  return res.status(200).json({
    success: true,
    message: 'AI Retail Automation API is working!',
    timestamp,
    environment: {
      retailcrm_configured: !!process.env.RETAILCRM_URL,
      supabase_configured: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
      telegram_configured: !!process.env.TELEGRAM_TOKEN,
      node_version: process.version
    },
    endpoints: {
      sync_orders: '/api/sync-orders',
      stats: '/api/stats',
      test: '/api/test'
    },
    usage: {
      manual_sync: 'GET /api/sync-orders',
      get_stats: 'GET /api/stats',
      cron_alternative: 'Use external service to call /api/sync-orders every 3 minutes'
    }
  })
}