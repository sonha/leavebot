from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Shift callback prefixes
SHIFT_PREFIX = "shift"

# Shift options
SHIFTS = {
    "sang": "Sáng",
    "chieu": "Chiều",
    "cangay": "Cả ngày"
}


def create_shift_keyboard(prefix: str = "start", date_str: str = "") -> InlineKeyboardMarkup:
    """
    Create shift selection keyboard.

    Args:
        prefix: "start" or "end" to indicate which date's shift
        date_str: Date string to display (e.g., "15/12")
    """
    title = f"Ngày {'bắt đầu' if prefix == 'start' else 'kết thúc'}"
    if date_str:
        title += f" ({date_str})"

    keyboard = [
        [
            InlineKeyboardButton(
                "🌅 Sáng",
                callback_data=f"{SHIFT_PREFIX}_{prefix}_sang"
            ),
            InlineKeyboardButton(
                "🌆 Chiều",
                callback_data=f"{SHIFT_PREFIX}_{prefix}_chieu"
            )
        ],
        [
            InlineKeyboardButton(
                "📅 Cả ngày",
                callback_data=f"{SHIFT_PREFIX}_{prefix}_cangay"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def parse_shift_callback(callback_data: str) -> dict:
    """
    Parse shift callback data.

    Returns:
        {
            "prefix": "start" or "end",
            "shift": "Sáng", "Chiều", or "Cả ngày"
        }
        or None if invalid
    """
    if not callback_data.startswith(SHIFT_PREFIX):
        return None

    parts = callback_data.split("_")
    if len(parts) < 3:
        return None

    prefix = parts[1]
    shift_key = parts[2]
    shift = SHIFTS.get(shift_key)

    if not shift:
        return None

    return {
        "prefix": prefix,
        "shift": shift
    }
