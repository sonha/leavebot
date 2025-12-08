import asyncio
from telegram import Bot
from bot.config import BOT_TOKEN

async def main():
    print(f"Checking updates for bot...")
    bot = Bot(token=BOT_TOKEN)
    try:
        updates = await bot.get_updates()
        print(f"Found {len(updates)} updates.")
        for u in updates:
            if u.effective_chat:
                print(f"Chat: '{u.effective_chat.title}' | ID: {u.effective_chat.id} | Type: {u.effective_chat.type}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
