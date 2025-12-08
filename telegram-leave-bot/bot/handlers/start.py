from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.services.google_sheet import get_employee_by_telegram


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    Auto-check if user's Telegram is registered in Nhân sự sheet.
    """
    user = update.effective_user
    telegram_username = f"@{user.username}" if user.username else None

    if not telegram_username:
        await update.message.reply_text(
            "❌ Bạn chưa có username Telegram.\n"
            "Vui lòng cài đặt username trong Telegram Settings để sử dụng bot."
        )
        return

    # Check if user is registered
    employee = await get_employee_by_telegram(telegram_username)

    if not employee:
        await update.message.reply_text(
            "❌ Telegram của bạn chưa được đăng ký trong hệ thống.\n"
            "Vui lòng liên hệ HR để được thêm vào danh sách nhân sự."
        )
        return

    # Store employee info in context for later use
    context.user_data["employee"] = employee

    name = employee.get("name", telegram_username)
    email = employee.get("email", "")

    manager_email = employee.get("manager_email", "Chưa cập nhật")

    await update.message.reply_text(
        f"✅ Xin chào {name}!\n"
        f"📧 Email: {email}\n"
        f"👤 Quản lý: {manager_email}\n\n"
        f"Sử dụng /nghiphep để xin nghỉ phép."
    )


def get_start_handler() -> CommandHandler:
    """Get the start command handler."""
    return CommandHandler("start", start_command)
