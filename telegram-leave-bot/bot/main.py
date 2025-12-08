import asyncio
import logging
from telegram.ext import Application

from bot.config import BOT_TOKEN, validate_config
from bot.handlers.start import get_start_handler
from bot.handlers.leave import get_leave_handler
from bot.handlers.approval import get_approval_handler
from bot.handlers.admin import get_admin_handler
from bot.services.reminder import setup_reminder_scheduler

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Validate configuration
    validate_config()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(get_start_handler())
    application.add_handler(get_leave_handler())
    application.add_handler(get_approval_handler())
    application.add_handler(get_admin_handler())

    # Set up reminder scheduler
    scheduler = setup_reminder_scheduler(application.bot)

    # Start scheduler when bot starts
    async def on_startup(app):
        scheduler.start()
        logger.info("Reminder scheduler started")

    async def on_shutdown(app):
        scheduler.shutdown()
        logger.info("Reminder scheduler stopped")

    application.post_init = on_startup
    application.post_shutdown = on_shutdown

    # Run the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
