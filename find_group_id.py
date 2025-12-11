"""
Script to find the correct group ID.
Add the bot to your group, then send any message in the group.
The bot will print the group ID.
"""
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from bot.config import BOT_TOKEN

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show chat information for any message received."""
    chat = update.effective_chat
    user = update.effective_user

    print("\n" + "=" * 60)
    print("📨 MESSAGE RECEIVED!")
    print("=" * 60)
    print(f"Chat Type: {chat.type}")
    print(f"Chat ID: {chat.id}")
    print(f"Chat Title: {chat.title if chat.title else 'N/A'}")
    print(f"User: {user.first_name} (@{user.username if user.username else 'N/A'})")
    print(f"Message: {update.message.text if update.message.text else '[non-text]'}")
    print("=" * 60)

    if chat.type in ['group', 'supergroup']:
        print(f"\n✅ GROUP FOUND!")
        print(f"   Add this to your .env file:")
        print(f"   APPROVAL_GROUP_ID={chat.id}")
        print("=" * 60)

        # Try to send a reply
        try:
            await update.message.reply_text(
                f"✅ Group ID found!\n\n"
                f"Chat ID: {chat.id}\n"
                f"Chat Title: {chat.title}\n\n"
                f"Add this to your .env file:\n"
                f"APPROVAL_GROUP_ID={chat.id}"
            )
        except Exception as e:
            print(f"❌ Could not reply: {e}")

def main():
    """Start the bot to listen for messages."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handler for all messages
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("\n" + "=" * 60)
    print("🤖 GROUP ID FINDER BOT STARTED")
    print("=" * 60)
    print(f"Bot: @xinnghii_bot")
    print(f"\nInstructions:")
    print(f"1. Make sure the bot is added to your approval group")
    print(f"2. Send any message in that group")
    print(f"3. The bot will print the group ID here")
    print(f"\nPress Ctrl+C to stop.")
    print("=" * 60 + "\n")

    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
