from telegram.error import TelegramError
import traceback
import logging
from bot.config import ADMIN_ID

async def global_error_handler(update, context):
    """Catch all errors and prevent bot from crashing."""
    logging.error("⚠️ Global error caught:", exc_info=context.error)

    # Send error notification to admin if ADMIN_ID is configured
    if ADMIN_ID:
        error_text = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Bot Error:\n```\n{error_text}\n```",
                parse_mode="Markdown"
            )
        except TelegramError:
            pass
