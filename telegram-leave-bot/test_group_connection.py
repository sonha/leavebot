"""
Test script to verify bot connection to the approval group.
This will attempt to send a test message to the group.
"""
import asyncio
from telegram import Bot
from bot.config import BOT_TOKEN, APPROVAL_GROUP_ID, APPROVAL_TOPIC_ID

async def test_group_connection():
    """Test if bot can send messages to the approval group."""
    bot = Bot(token=BOT_TOKEN)

    print("=" * 50)
    print("Testing Bot Connection to Approval Group")
    print("=" * 50)
    print(f"\nBot Token: {BOT_TOKEN[:20]}...")
    print(f"Approval Group ID: {APPROVAL_GROUP_ID}")
    print(f"Approval Topic ID: {APPROVAL_TOPIC_ID}")
    print("\n" + "=" * 50)

    try:
        # Get bot info
        me = await bot.get_me()
        print(f"\n✅ Bot Info:")
        print(f"   Username: @{me.username}")
        print(f"   Name: {me.first_name}")
        print(f"   ID: {me.id}")

        # Try to get chat info
        print(f"\n📡 Attempting to get chat info...")
        chat = await bot.get_chat(chat_id=APPROVAL_GROUP_ID)
        print(f"\n✅ Chat Found:")
        print(f"   Title: {chat.title}")
        print(f"   Type: {chat.type}")
        print(f"   ID: {chat.id}")

        # Try to send a test message
        print(f"\n📤 Attempting to send test message...")
        message = await bot.send_message(
            chat_id=APPROVAL_GROUP_ID,
            text="🧪 Test message from bot!\n\nThis is a test to verify bot connection.\nIf you see this, the bot is working correctly! ✅",
            message_thread_id=APPROVAL_TOPIC_ID
        )
        print(f"\n✅ SUCCESS! Test message sent!")
        print(f"   Message ID: {message.message_id}")
        print(f"   Chat ID: {message.chat.id}")

        print("\n" + "=" * 50)
        print("✅ All tests passed! Bot can connect to the group.")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nPossible solutions:")
        print(f"1. Make sure the bot is added to the group")
        print(f"2. Make sure the bot has permission to send messages")
        print(f"3. Verify the group ID is correct: {APPROVAL_GROUP_ID}")
        print(f"4. If using topics, verify topic ID: {APPROVAL_TOPIC_ID}")
        print("=" * 50)
        raise

if __name__ == "__main__":
    asyncio.run(test_group_connection())
