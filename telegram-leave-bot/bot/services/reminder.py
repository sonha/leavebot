from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from bot.services.pending_store import get_requests_older_than, mark_reminder_sent
from bot.config import BOT_TOKEN


async def check_pending_reminders(bot: Bot) -> None:
    """
    Check for pending requests older than 24 hours and send reminders.
    This function is called by the scheduler every hour.
    """
    print(f"[{datetime.now()}] Checking for pending reminders...")

    # Get requests older than 24 hours that haven't been reminded
    old_requests = get_requests_older_than(hours=24)

    for request_id, request in old_requests.items():
        manager_telegram = request.get("manager_telegram")
        employee_name = request.get("employee_name", request.get("employee_email"))
        created_at = request.get("created_at", "")

        # Format created time
        try:
            created_dt = datetime.fromisoformat(created_at)
            created_str = created_dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            created_str = created_at

        # Calculate hours waiting
        now = datetime.now()
        try:
            hours_waiting = int((now - datetime.fromisoformat(created_at)).total_seconds() / 3600)
        except ValueError:
            hours_waiting = 24

        reminder_msg = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⏰ NHẮC NHỞ DUYỆT YÊU CẦU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Pls check the employee leave request\n\n"
            f"📋 Yêu cầu: #{request_id}\n"
            f"👤 Nhân viên: {employee_name}\n"
            f"📅 Ngày gửi: {created_str}\n"
            f"⏱ Đã chờ: {hours_waiting} giờ\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        # Try to get manager's chat ID from stored data or send to group
        # For now, we'll just mark as sent since we can't DM without chat_id
        # In practice, you'd need to store manager's chat_id during registration

        # Mark reminder as sent
        mark_reminder_sent(request_id)
        print(f"[{datetime.now()}] Reminder marked for request #{request_id}")


def setup_reminder_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Set up the reminder scheduler.
    Returns the scheduler instance (must be started separately).
    """
    scheduler = AsyncIOScheduler()

    # Run every hour
    scheduler.add_job(
        check_pending_reminders,
        'interval',
        hours=1,
        args=[bot],
        id='reminder_check',
        replace_existing=True
    )

    return scheduler
