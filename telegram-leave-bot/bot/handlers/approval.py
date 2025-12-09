from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.services.pending_store import get_request, delete_request
from bot.services.google_sheet import approve_leave, get_employee_by_telegram
from bot.utils.date_utils import format_date

# Vietnam timezone (UTC+7)
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle approve/reject button clicks in approval group."""
    query = update.callback_query
    user = update.effective_user
    user_telegram = f"@{user.username}" if user.username else None

    # Parse callback data
    data = query.data
    if data.startswith("approve_"):
        action = "approve"
        request_id = data.replace("approve_", "")
    elif data.startswith("reject_"):
        action = "reject"
        request_id = data.replace("reject_", "")
    else:
        await query.answer("❌ Lỗi: Không xác định được hành động.")
        return

    # Get pending request
    request = get_request(request_id)
    if not request:
        await query.answer("❌ Yêu cầu không tồn tại hoặc đã được xử lý.", show_alert=True)
        return

    # Check authorization - only assigned manager can approve/reject
    manager_telegram = request.get("manager_telegram")
    if user_telegram != manager_telegram:
        await query.answer(
            "❌ Bạn không có quyền duyệt yêu cầu này.\n"
            "Chỉ quản lý được chỉ định mới có thể duyệt.",
            show_alert=True
        )
        return

    if action == "approve":
        await process_approval(query, context, request_id, request, user_telegram)
    else:
        await process_rejection(query, context, request_id, request, user_telegram)


async def process_approval(query, context, request_id: str, request: dict, approver: str) -> None:
    """Process leave request approval."""
    await query.answer("✅ Đang xử lý...")

    # Prepare data for Google Sheet
    now = datetime.now(VN_TZ)
    approval_data = {
        "employee_email": request.get("employee_email"),
        "manager_email": request.get("manager_email"),
        "leave_type": request.get("leave_type"),
        "start_date": request.get("start_date"),
        "start_shift": request.get("start_shift"),
        "end_date": request.get("end_date"),
        "end_shift": request.get("end_shift"),
        "reason": request.get("reason"),
        "created_at": request.get("created_at"),
        "approved_by": request.get("manager_email"),
        "approved_at": now.isoformat()
    }

    # Write to Google Sheet
    success = await approve_leave(approval_data)

    if not success:
        # Since we already called answer("Processing"), we cannot call it again for an alert.
        # We must send a message or edit the text.
        try:
            await query.message.reply_text("❌ Lỗi khi ghi vào hệ thống. Vui lòng thử lại sau.")
        except Exception:
            pass # Ignore if we can't reply
        return

    # Delete from pending requests
    delete_request(request_id)

    # Update message in group
    employee_name = request.get("employee_name", request.get("employee_email"))
    start_date = request.get("start_date")
    end_date = request.get("end_date")

    date_range = format_date(start_date)
    if end_date:
        date_range += f" - {format_date(end_date)}"

    updated_msg = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ ĐÃ DUYỆT #{request_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Người gửi: {employee_name}\n"
        f"📌 Loại: {request.get('leave_type')}\n"
        f"📅 {date_range}\n"
        f"📅 Từ: {format_date(start_date)} ({leave_req['start_shift']})\n"
        f"📝 Lý do: {leave_req['reason']}\n"
        f"🕐 Gửi lúc: {datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M')}\n"
        f"✅ Duyệt bởi: {approver} ({now.strftime('%d/%m/%Y %H:%M')})\n"
    )

    await query.edit_message_text(updated_msg)

    # Notify employee via DM
    user_chat_id = request.get("user_chat_id")
    if user_chat_id:
        try:
            await context.bot.send_message(
                chat_id=user_chat_id,
                text=f"✅ Yêu cầu #{request_id} đã được duyệt!"
            )
        except Exception as e:
            print(f"Error sending DM to user: {e}")


async def process_rejection(query, context, request_id: str, request: dict, rejector: str) -> None:
    """Process leave request rejection."""
    await query.answer("❌ Đang xử lý...")

    # Delete from pending requests (not written to Raw sheet)
    delete_request(request_id)

    # Update message in group
    employee_name = request.get("employee_name", request.get("employee_email"))
    start_date = request.get("start_date")
    end_date = request.get("end_date")
    now = datetime.now()

    date_range = format_date(start_date)
    if end_date:
        date_range += f" - {format_date(end_date)}"

    updated_msg = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"❌ TỪ CHỐI #{request_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Người gửi: {employee_name}\n"
        f"📌 Loại: {request.get('leave_type')}\n"
        f"📅 {date_range}\n"
        f"❌ Từ chối bởi: {rejector} ({now.strftime('%d/%m/%Y %H:%M')})\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    await query.edit_message_text(updated_msg)

    # Notify employee via DM
    user_chat_id = request.get("user_chat_id")
    if user_chat_id:
        try:
            await context.bot.send_message(
                chat_id=user_chat_id,
                text=f"❌ Yêu cầu #{request_id} đã bị từ chối."
            )
        except Exception as e:
            print(f"Error sending DM to user: {e}")


def get_approval_handler() -> CallbackQueryHandler:
    """Get the approval callback handler."""
    return CallbackQueryHandler(handle_approval, pattern="^(approve_|reject_)")
