from datetime import datetime, date


def format_date(d: date | datetime | str) -> str:
    """Format date as dd/MM/yyyy."""
    if isinstance(d, str):
        # Try to parse ISO format
        try:
            d = datetime.fromisoformat(d).date()
        except ValueError:
            return d
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d/%m/%Y")


def format_date_short(d: date | datetime | str) -> str:
    """Format date as dd/MM."""
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d).date()
        except ValueError:
            return d
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d/%m")


def parse_date(date_str: str) -> date:
    """Parse date from dd/MM/yyyy or yyyy-MM-dd format."""
    for fmt in ["%d/%m/%Y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def is_weekend(d: date | datetime) -> bool:
    """Check if date is weekend (Saturday or Sunday)."""
    if isinstance(d, datetime):
        d = d.date()
    return d.weekday() >= 5  # 5=Saturday, 6=Sunday


def calculate_working_days(start_date: date, end_date: date = None) -> float:
    """
    Calculate number of working days between dates (excluding weekends).
    If end_date is None, returns 1 for single day (or 0 if weekend).
    """
    if end_date is None:
        return 0 if is_weekend(start_date) else 1

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    days = 0
    current = start_date
    while current <= end_date:
        if not is_weekend(current):
            days += 1
        current = date(current.year, current.month, current.day)
        current = date.fromordinal(current.toordinal() + 1)

    return days


def calculate_leave_days(
    start_date: date,
    start_shift: str,
    end_date: date = None,
    end_shift: str = None
) -> float:
    """
    Calculate total leave days based on dates and shifts.

    Args:
        start_date: Start date
        start_shift: "Sáng", "Chiều", or "Cả ngày"
        end_date: End date (optional, for single day leave)
        end_shift: "Sáng", "Chiều", or "Cả ngày" (optional)

    Returns:
        Number of leave days (can be 0.5 increments)
    """
    # Single day leave
    if end_date is None or start_date == end_date:
        if is_weekend(start_date):
            return 0
        if start_shift == "Cả ngày":
            return 1
        return 0.5

    # Multi-day leave
    total_days = calculate_working_days(start_date, end_date)

    # Adjust for shifts
    if start_shift == "Chiều" and not is_weekend(start_date):
        total_days -= 0.5

    if end_shift and end_shift == "Sáng" and not is_weekend(end_date):
        total_days -= 0.5

    return max(0, total_days)
