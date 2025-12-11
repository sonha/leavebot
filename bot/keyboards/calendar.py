from datetime import datetime, timedelta
from calendar import monthrange
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Callback data prefixes
CAL_PREV_MONTH = "cal_prev"
CAL_NEXT_MONTH = "cal_next"
CAL_DAY = "cal_day"
CAL_IGNORE = "cal_ignore"
CAL_SINGLE_DAY = "cal_single"
CAL_DATE_RANGE = "cal_range"

# Vietnamese day names
DAYS_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

# Vietnamese month names
MONTHS_VI = [
    "", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
    "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"
]


def create_calendar(
    year: int = None,
    month: int = None,
    prefix: str = "start",
    show_range_options: bool = True
) -> InlineKeyboardMarkup:
    """
    Create a calendar inline keyboard.

    Args:
        year: Year to display (defaults to current)
        month: Month to display (defaults to current)
        prefix: Callback prefix ("start" or "end")
        show_range_options: Whether to show single/range buttons

    Returns:
        InlineKeyboardMarkup with calendar
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    keyboard = []

    # Month/Year header with navigation
    header_row = [
        InlineKeyboardButton("◀", callback_data=f"{prefix}_{CAL_PREV_MONTH}_{year}_{month}"),
        InlineKeyboardButton(f"{MONTHS_VI[month]} {year}", callback_data=CAL_IGNORE),
        InlineKeyboardButton("▶", callback_data=f"{prefix}_{CAL_NEXT_MONTH}_{year}_{month}")
    ]
    keyboard.append(header_row)

    # Day names header
    day_row = [InlineKeyboardButton(day, callback_data=CAL_IGNORE) for day in DAYS_VI]
    keyboard.append(day_row)

    # Get first day of month and number of days
    first_day_weekday = datetime(year, month, 1).weekday()  # 0=Monday
    num_days = monthrange(year, month)[1]

    # Build calendar grid
    day = 1
    for week in range(6):  # Max 6 weeks
        row = []
        for weekday in range(7):
            if week == 0 and weekday < first_day_weekday:
                # Empty cell before first day
                row.append(InlineKeyboardButton(" ", callback_data=CAL_IGNORE))
            elif day > num_days:
                # Empty cell after last day
                row.append(InlineKeyboardButton(" ", callback_data=CAL_IGNORE))
            else:
                # Check if it's weekend (Saturday=5, Sunday=6)
                is_weekend = weekday >= 5
                day_str = str(day)

                # Check if it's today
                is_today = (year == now.year and month == now.month and day == now.day)

                # Format day display
                if is_today:
                    display = f"[{day_str}]"
                elif is_weekend:
                    display = f"({day_str})"
                else:
                    display = day_str

                callback = f"{prefix}_{CAL_DAY}_{year}_{month}_{day}"
                row.append(InlineKeyboardButton(display, callback_data=callback))
                day += 1

        keyboard.append(row)
        if day > num_days:
            break

    # Single day / Date range options (only for start date)
    if show_range_options and prefix == "start":
        options_row = [
            InlineKeyboardButton("📅 Chỉ 1 ngày", callback_data=f"{prefix}_{CAL_SINGLE_DAY}"),
            InlineKeyboardButton("📅 Chọn khoảng ngày", callback_data=f"{prefix}_{CAL_DATE_RANGE}")
        ]
        keyboard.append(options_row)

    return InlineKeyboardMarkup(keyboard)


def parse_calendar_callback(callback_data: str) -> dict:
    """
    Parse calendar callback data.

    Returns:
        {
            "prefix": "start" or "end",
            "action": "prev", "next", "day", "single", "range",
            "year": int (optional),
            "month": int (optional),
            "day": int (optional)
        }
    """
    parts = callback_data.split("_")

    if len(parts) < 3:
        return {"action": "ignore"}

    prefix = parts[0]
    action_type = parts[1] + "_" + parts[2] if len(parts) > 2 else parts[1]

    result = {"prefix": prefix}

    if action_type == CAL_PREV_MONTH:
        result["action"] = "prev"
        result["year"] = int(parts[3])
        result["month"] = int(parts[4])
    elif action_type == CAL_NEXT_MONTH:
        result["action"] = "next"
        result["year"] = int(parts[3])
        result["month"] = int(parts[4])
    elif action_type == CAL_DAY:
        result["action"] = "day"
        result["year"] = int(parts[3])
        result["month"] = int(parts[4])
        result["day"] = int(parts[5])
    elif action_type == CAL_SINGLE_DAY:
        result["action"] = "single"
    elif action_type == CAL_DATE_RANGE:
        result["action"] = "range"
    else:
        result["action"] = "ignore"

    return result


def get_prev_month(year: int, month: int) -> tuple:
    """Get previous month and year."""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def get_next_month(year: int, month: int) -> tuple:
    """Get next month and year."""
    if month == 12:
        return year + 1, 1
    return year, month + 1
