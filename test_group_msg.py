import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
APPROVAL_GROUP_ID = os.getenv("APPROVAL_GROUP_ID")
APPROVAL_TOPIC_ID = os.getenv("APPROVAL_TOPIC_ID")

async def test_send():
    print(f"Testing with Token: {BOT_TOKEN[:10]}...")
    print(f"Group ID: {APPROVAL_GROUP_ID}")
    print(f"Topic ID: {APPROVAL_TOPIC_ID}")

    bot = Bot(token=BOT_TOKEN)
    
    try:
        topic_id = int(APPROVAL_TOPIC_ID) if APPROVAL_TOPIC_ID else None
        print("Sending message...")
        msg = await bot.send_message(
            chat_id=APPROVAL_GROUP_ID,
            text="✅ Test message from Leave Bot verifying permissions.",
            message_thread_id=topic_id
        )
        print(f"✅ Message sent successfully! Message ID: {msg.message_id}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

if __name__ == "__main__":
    asyncio.run(test_send())
