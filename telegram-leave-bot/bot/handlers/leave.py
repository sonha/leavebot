from datetime import datetime, date
from zoneinfo import ZoneInfo
import logging

# Vietnam timezone (UTC+7)
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from bot.services.google_sheet import get_employee_by_telegram, get_manager_telegram
from bot.services.pending_store import generate_request_id, save_request
from bot.keyboards.calendar import (
    create_calendar,
    parse_calendar_callback,
    get_prev_month,
    get_next_month
)
from bot.keyboards.leave_type import create_leave_type_keyboard, parse_leave_type_callback
from bot.keyboards.shift import create_shift_keyboard, parse_shift_callback
from bot.utils.date_utils import format_date, format_date_short, calculate_leave_days
from bot.config import APPROVAL_GROUP_ID, APPROVAL_TOPIC_ID


# Conversation states
(
    SELECT_LEAVE_TYPE,
    SELECT_START_DATE,
    SELECT_DATE_MODE,
    SELECT_END_DATE,
    SELECT_START_SHIFT,
    SELECT_END_SHIFT,
    INPUT_MINUTES,
    INPUT_REASON,
    CONFIRM
) = range(9)


async def nghiphep_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /nghiphep command - start leave request flow."""
    # Only allow in private chat
    if update.effective_chat.type != "private":
        return ConversationHandler.END

    user = update.effective_user
    telegram_username = f"@{user.username}" if user.username else None

    if not telegram_username:
        await update.message.reply_text(
            "❌ Bạn chưa có username Telegram.\n"
            "Vui lòng cài đặt username trong Telegram Settings."
        )
        return ConversationHandler.END

    # Check if user is registered
    employee = await get_employee_by_telegram(telegram_username)

    if not employee:
        await update.message.reply_text(
            "❌ Telegram của bạn chưa được đăng ký trong hệ thống.\n"
            "Vui lòng liên hệ HR để được thêm vào danh sách nhân sự."
        )
        return ConversationHandler.END

    # Check if manager is in system
    manager_email = employee.get("manager_email")
    if manager_email:
        manager_telegram = await get_manager_telegram(manager_email)
        if not manager_telegram:
            await update.message.reply_text(
                "❌ Quản lý của bạn chưa có Telegram trong hệ thống.\n"
                "Vui lòng liên hệ HR để được hỗ trợ."
            )
            return ConversationHandler.END
        employee["manager_telegram"] = manager_telegram

    # Store employee info
    context.user_data["employee"] = employee
    context.user_data["leave_request"] = {}

    await update.message.reply_text(
        "📋 CHỌN LOẠI NGHỈ",
        reply_markup=create_leave_type_keyboard()
    )

    return SELECT_LEAVE_TYPE


async def select_leave_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle leave type selection."""
    query = update.callback_query
    await query.answer()

    leave_type = parse_leave_type_callback(query.data)
    if not leave_type:
        return SELECT_LEAVE_TYPE

    context.user_data["leave_request"]["leave_type"] = leave_type

    await query.edit_message_text(
        f"✅ Loại nghỉ: {leave_type}\n\n"
        "📅 CHỌN NGÀY BẮT ĐẦU",
        reply_markup=create_calendar(prefix="start", show_range_options=False)
    )

    return SELECT_START_DATE


async def handle_start_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle start date calendar navigation and selection."""
    query = update.callback_query
    await query.answer()

    parsed = parse_calendar_callback(query.data)
    action = parsed.get("action")

    if action == "ignore":
        return SELECT_START_DATE

    if action == "prev":
        year, month = get_prev_month(parsed["year"], parsed["month"])
        await query.edit_message_reply_markup(
            reply_markup=create_calendar(year, month, prefix="start", show_range_options=False)
        )
        return SELECT_START_DATE

    if action == "next":
        year, month = get_next_month(parsed["year"], parsed["month"])
        await query.edit_message_reply_markup(
            reply_markup=create_calendar(year, month, prefix="start", show_range_options=False)
        )
        return SELECT_START_DATE

    if action == "day":
        selected_date = date(parsed["year"], parsed["month"], parsed["day"])
        context.user_data["leave_request"]["start_date"] = selected_date.isoformat()

        leave_type = context.user_data["leave_request"].get("leave_type")

        # For Đi muộn/Về sớm - skip date mode, go directly to shift selection
        if leave_type in ["Đi muộn", "Về sớm"]:
            context.user_data["leave_request"]["end_date"] = None
            date_str = format_date_short(selected_date)

            await query.edit_message_text(
                f"⏰ CHỌN CA LÀM VIỆC\n"
                f"Ngày: {format_date(selected_date)}",
                reply_markup=create_shift_keyboard(prefix="start", date_str=date_str)
            )

            return SELECT_START_SHIFT

        # Ask if single day or date range
        keyboard = [
            [
                InlineKeyboardButton("📅 Chỉ 1 ngày", callback_data="mode_single"),
                InlineKeyboardButton("📅 Chọn khoảng ngày", callback_data="mode_range")
            ]
        ]

        await query.edit_message_text(
            f"✅ Ngày bắt đầu: {format_date(selected_date)}\n\n"
            "Bạn muốn nghỉ:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SELECT_DATE_MODE

    return SELECT_START_DATE


async def select_date_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle single day vs date range selection."""
    query = update.callback_query
    await query.answer()

    if query.data == "mode_single":
        # Single day - skip end date, go to shift selection
        context.user_data["leave_request"]["end_date"] = None

        start_date = context.user_data["leave_request"]["start_date"]
        date_str = format_date_short(start_date)

        await query.edit_message_text(
            f"⏰ CHỌN CA LÀM VIỆC\n"
            f"Ngày: {format_date(start_date)}",
            reply_markup=create_shift_keyboard(prefix="start", date_str=date_str)
        )

        return SELECT_START_SHIFT

    elif query.data == "mode_range":
        # Date range - select end date
        await query.edit_message_text(
            "📅 CHỌN NGÀY KẾT THÚC",
            reply_markup=create_calendar(prefix="end", show_range_options=False)
        )

        return SELECT_END_DATE

    return SELECT_DATE_MODE


async def handle_end_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle end date calendar navigation and selection."""
    query = update.callback_query
    await query.answer()

    parsed = parse_calendar_callback(query.data)
    action = parsed.get("action")

    if action == "ignore":
        return SELECT_END_DATE

    if action == "prev":
        year, month = get_prev_month(parsed["year"], parsed["month"])
        await query.edit_message_reply_markup(
            reply_markup=create_calendar(year, month, prefix="end", show_range_options=False)
        )
        return SELECT_END_DATE

    if action == "next":
        year, month = get_next_month(parsed["year"], parsed["month"])
        await query.edit_message_reply_markup(
            reply_markup=create_calendar(year, month, prefix="end", show_range_options=False)
        )
        return SELECT_END_DATE

    if action == "day":
        selected_date = date(parsed["year"], parsed["month"], parsed["day"])
        start_date = date.fromisoformat(context.user_data["leave_request"]["start_date"])

        # Validate end date is after start date
        if selected_date < start_date:
            await query.answer("❌ Ngày kết thúc phải sau ngày bắt đầu!", show_alert=True)
            return SELECT_END_DATE

        context.user_data["leave_request"]["end_date"] = selected_date.isoformat()

        date_str = format_date_short(start_date)
        await query.edit_message_text(
            f"⏰ CHỌN CA LÀM VIỆC\n"
            f"Ngày bắt đầu: {format_date(start_date)}",
            reply_markup=create_shift_keyboard(prefix="start", date_str=date_str)
        )

        return SELECT_START_SHIFT

    return SELECT_END_DATE


async def select_start_shift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle start shift selection."""
    query = update.callback_query
    await query.answer()

    parsed = parse_shift_callback(query.data)
    if not parsed:
        return SELECT_START_SHIFT

    context.user_data["leave_request"]["start_shift"] = parsed["shift"]

    end_date = context.user_data["leave_request"].get("end_date")
    leave_type = context.user_data["leave_request"].get("leave_type")

    if end_date:
        # Multi-day - ask for end shift
        date_str = format_date_short(end_date)
        await query.edit_message_text(
            f"⏰ CHỌN CA KẾT THÚC\n"
            f"Ngày kết thúc: {format_date(end_date)}",
            reply_markup=create_shift_keyboard(prefix="end", date_str=date_str)
        )
        return SELECT_END_SHIFT
    else:
        # Single day
        context.user_data["leave_request"]["end_shift"] = None

        # Check if Đi muộn or Về sớm - need to input minutes
        if leave_type in ["Đi muộn", "Về sớm"]:
            await query.edit_message_text(
                "⏱ NHẬP SỐ PHÚT\n"
                f"Vui lòng nhập số phút {leave_type.lower()}:"
            )
            return INPUT_MINUTES

        await query.edit_message_text(
            "📝 NHẬP LÝ DO\n"
            "Vui lòng nhập lý do nghỉ:"
        )

        return INPUT_REASON


async def select_end_shift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle end shift selection."""
    query = update.callback_query
    await query.answer()

    parsed = parse_shift_callback(query.data)
    if not parsed:
        return SELECT_END_SHIFT

    context.user_data["leave_request"]["end_shift"] = parsed["shift"]

    await query.edit_message_text(
        "📝 NHẬP LÝ DO\n"
        "Vui lòng nhập lý do nghỉ:"
    )

    return INPUT_REASON


async def input_minutes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle minutes input for Đi muộn/Về sớm."""
    text = update.message.text.strip()

    # Validate that input is a number
    try:
        minutes = int(text)
        if minutes <= 0:
            await update.message.reply_text("❌ Số phút phải lớn hơn 0. Vui lòng nhập lại:")
            return INPUT_MINUTES
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số phút hợp lệ (ví dụ: 15, 30, 45):")
        return INPUT_MINUTES

    context.user_data["leave_request"]["leave_minutes"] = minutes

    await update.message.reply_text(
        "📝 NHẬP LÝ DO\n"
        "Vui lòng nhập lý do:"
    )

    return INPUT_REASON


async def input_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle reason text input."""
    reason = update.message.text.strip()

    if not reason:
        await update.message.reply_text("❌ Vui lòng nhập lý do nghỉ.")
        return INPUT_REASON

    context.user_data["leave_request"]["reason"] = reason

    # Show confirmation
    leave_req = context.user_data["leave_request"]
    start_date = date.fromisoformat(leave_req["start_date"])
    end_date = date.fromisoformat(leave_req["end_date"]) if leave_req.get("end_date") else None

    # Calculate leave days
    num_days = calculate_leave_days(
        start_date,
        leave_req["start_shift"],
        end_date,
        leave_req.get("end_shift")
    )

    # Build confirmation message
    leave_type = leave_req['leave_type']
    msg = (
        "📋 XÁC NHẬN THÔNG TIN\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Loại: {leave_type}\n"
        f"📅 Từ: {format_date(start_date)} ({leave_req['start_shift']})\n"
    )

    if end_date:
        msg += f"📅 Đến: {format_date(end_date)} ({leave_req['end_shift']})\n"

    # Show minutes for Đi muộn/Về sớm, otherwise show days
    if leave_type in ["Đi muộn", "Về sớm"]:
        msg += f"⏱ Số phút: {leave_req.get('leave_minutes', 0)} phút\n"
    else:
        msg += f"⏱ Số ngày: {num_days} ngày\n"

    msg += (
        f"📝 Lý do: {reason}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Gửi yêu cầu", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Hủy", callback_data="confirm_no")
        ]
    ]

    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CONFIRM


async def confirm_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of leave request."""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        await query.edit_message_text("❌ Đã hủy yêu cầu nghỉ phép.")
        return ConversationHandler.END

    if query.data == "confirm_yes":
        try:
            employee = context.user_data["employee"]
            leave_req = context.user_data["leave_request"]

            # Generate request ID
            request_id = generate_request_id()

            # Prepare request data
            request_data = {
                "employee_email": employee.get("email"),
                "employee_telegram": f"@{update.effective_user.username}",
                "employee_name": employee.get("name"),
                "manager_email": employee.get("manager_email"),
                "manager_telegram": employee.get("manager_telegram"),
                "leave_type": leave_req["leave_type"],
                "start_date": leave_req["start_date"],
                "start_shift": leave_req["start_shift"],
                "end_date": leave_req.get("end_date"),
                "end_shift": leave_req.get("end_shift"),
                "leave_minutes": leave_req.get("leave_minutes"),
                "reason": leave_req["reason"],
                "user_chat_id": update.effective_chat.id
            }

            # Save to pending requests
            save_request(request_id, request_data)

            # Calculate leave days
            start_date = date.fromisoformat(leave_req["start_date"])
            end_date = date.fromisoformat(leave_req["end_date"]) if leave_req.get("end_date") else None
            num_days = calculate_leave_days(
                start_date,
                leave_req["start_shift"],
                end_date,
                leave_req.get("end_shift")
            )

            # Send to approval group
            manager_tag = employee.get("manager_telegram", "")
            leave_type = leave_req['leave_type']

            approval_msg = (
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 YÊU CẦU NGHỈ PHÉP #{request_id}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Người gửi: {employee.get('name')} ({employee.get('email')})\n"
                f"👔 Quản lý: {manager_tag}\n"
                f"📌 Loại: {leave_type}\n"
                f"📅 Từ: {format_date(start_date)} ({leave_req['start_shift']})\n"
            )

            if end_date:
                approval_msg += f"📅 Đến: {format_date(end_date)} ({leave_req['end_shift']})\n"

            # Show minutes for Đi muộn/Về sớm
            if leave_type in ["Đi muộn", "Về sớm"]:
                approval_msg += f"⏱ Số phút: {leave_req.get('leave_minutes', 0)} phút\n"

            approval_msg += (
                f"📝 Lý do: {leave_req['reason']}\n"
                f"🕐 Gửi lúc: {datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M')}\n"
            )

            keyboard = [
                [
                    InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_{request_id}"),
                    InlineKeyboardButton("❌ Từ chối", callback_data=f"reject_{request_id}")
                ]
            ]

            # Send to approval group (with topic support)
            sent_msg = await context.bot.send_message(
                chat_id=APPROVAL_GROUP_ID,
                text=approval_msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                message_thread_id=APPROVAL_TOPIC_ID
            )

            # Update pending request with message ID
            from bot.services.pending_store import update_request
            update_request(request_id, {"message_id": sent_msg.message_id})

            # Confirm to user
            await query.edit_message_text(
                f"✅ Đã gửi yêu cầu nghỉ phép!\n"
                f"📋 Mã yêu cầu: #{request_id}\n"
                f"⏳ Đang chờ phê duyệt từ quản lý."
            )

            return ConversationHandler.END

        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in confirm_request: {e}", exc_info=True)

            # Inform user of the error
            try:
                await query.edit_message_text(
                    f"❌ Có lỗi xảy ra khi gửi yêu cầu!\n"
                    f"Chi tiết lỗi: {str(e)}\n\n"
                    f"Vui lòng thử lại hoặc liên hệ admin."
                )
            except:
                await update.effective_chat.send_message(
                    f"❌ Có lỗi xảy ra khi gửi yêu cầu!\n"
                    f"Chi tiết lỗi: {str(e)}\n\n"
                    f"Vui lòng thử lại hoặc liên hệ admin."
                )
            return ConversationHandler.END

    return CONFIRM


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("❌ Đã hủy yêu cầu.")
    return ConversationHandler.END


def get_leave_handler() -> ConversationHandler:
    """Get the leave request conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("nghiphep", nghiphep_command)],
        states={
            SELECT_LEAVE_TYPE: [
                CallbackQueryHandler(select_leave_type, pattern="^leave_type_")
            ],
            SELECT_START_DATE: [
                CallbackQueryHandler(handle_start_calendar, pattern="^start_")
            ],
            SELECT_DATE_MODE: [
                CallbackQueryHandler(select_date_mode, pattern="^mode_")
            ],
            SELECT_END_DATE: [
                CallbackQueryHandler(handle_end_calendar, pattern="^end_")
            ],
            SELECT_START_SHIFT: [
                CallbackQueryHandler(select_start_shift, pattern="^shift_start_")
            ],
            SELECT_END_SHIFT: [
                CallbackQueryHandler(select_end_shift, pattern="^shift_end_")
            ],
            INPUT_MINUTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_minutes)
            ],
            INPUT_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_reason)
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_request, pattern="^confirm_")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
