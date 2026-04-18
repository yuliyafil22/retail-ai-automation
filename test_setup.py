import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))


def test_setup():
    print("🔍 Testing AI automation system...")

    try:
        from config.settings import settings
        print("✅ Settings loaded")
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return

    # Test Telegram with direct import
    try:
        from integrations.telegram import TelegramClient  # Direct import
        telegram = TelegramClient()

        if telegram.send_message("🧪 AI System Test - All Working!"):
            print("✅ Telegram works")
        else:
            print("❌ Telegram error")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

    # Test Supabase
    try:
        from integrations.supabase_client import SupabaseClient
        supabase = SupabaseClient()

        print("\n🔍 Checking ai_orders table...")
        structure = supabase.check_table_structure()
        print(f"✅ Table status: {structure.get('status')}")

        # Test statistics
        print("\n📊 Current statistics...")
        stats = supabase.get_today_stats()
        print(f"📦 Orders today: {stats.get('orders_count', 0)}")
        print(f"💰 Total sum: {stats.get('total_sum', 0):,.0f} ₸")
        print(f"📈 Average order: {stats.get('avg_order', 0):,.0f} ₸")

    except Exception as e:
        print(f"❌ Supabase error: {e}")


if __name__ == "__main__":
    test_setup()