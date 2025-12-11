from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.services.google_sheet import clear_employee_cache, get_all_employees_cached

# List of admin Telegram usernames (without @)
ADMIN_USERNAMES = ["jonestrinh"]  # Replace with actual admin usernames


async def read_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Admin command to manually refresh Google Sheets cache.
    Usage: /read
    """
    user = update.effective_user
    username = user.username

    # Check if user is admin
    if username not in ADMIN_USERNAMES:
        await update.message.reply_text(
            "❌ Bạn không có quyền sử dụng lệnh này.\n"
            "Chỉ admin mới có thể làm mới dữ liệu."
        )
        return

    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Đang đọc dữ liệu từ Google Sheets...")

    try:
        # Clear cache
        clear_employee_cache()

        # Fetch fresh data
        employees = await get_all_employees_cached()

        # Send success message
        await processing_msg.edit_text(
            f"✅ Đã làm mới dữ liệu thành công!\n\n"
            f"📊 Tổng số nhân viên: {len(employees)}\n"
            f"👤 Nhân viên đang làm việc: {len([e for e in employees if e.get('is_working')])}\n"
            f"🕐 Cập nhật lúc: {context.bot_data.get('cache_time', 'N/A')}"
        )

    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Lỗi khi đọc dữ liệu!\n\n"
            f"Chi tiết: {str(e)}"
        )


def get_admin_handler():
    """Get the admin command handler."""
    return CommandHandler("read", read_command)
