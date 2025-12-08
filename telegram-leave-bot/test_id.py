import asyncio
from telegram import Bot
from bot.config import BOT_TOKEN

# Suspected correct ID
TEST_ID = -1003415127720

async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        print(f"Attempting to send to {TEST_ID}...")
        await bot.send_message(chat_id=TEST_ID, text="🔔 Testing Bot Config: Success!")
        print("✅ Message sent successfully!")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
