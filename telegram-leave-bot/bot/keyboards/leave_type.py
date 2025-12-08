from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Leave type callback prefixes
LEAVE_TYPE_PREFIX = "leave_type"

# Leave types
LEAVE_TYPES = {
    "wfh": "WFH",
    "nghiphep": "Nghỉ phép",
    "nghikhongluong": "Nghỉ không lương"
}


def create_leave_type_keyboard() -> InlineKeyboardMarkup:
    """Create leave type selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                "🏠 WFH",
                callback_data=f"{LEAVE_TYPE_PREFIX}_wfh"
            )
        ],
        [
            InlineKeyboardButton(
                "🌴 Nghỉ phép",
                callback_data=f"{LEAVE_TYPE_PREFIX}_nghiphep"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 Nghỉ không lương",
                callback_data=f"{LEAVE_TYPE_PREFIX}_nghikhongluong"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def parse_leave_type_callback(callback_data: str) -> str:
    """
    Parse leave type callback data.

    Returns:
        Leave type string (e.g., "WFH", "Nghỉ phép", "Nghỉ không lương")
        or None if invalid
    """
    if not callback_data.startswith(LEAVE_TYPE_PREFIX):
        return None

    parts = callback_data.split("_")
    if len(parts) < 3:
        return None

    type_key = parts[2]
    return LEAVE_TYPES.get(type_key)
