import json
from datetime import datetime
from typing import Optional
from pathlib import Path

# Path to pending requests JSON file
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PENDING_FILE = DATA_DIR / "pending_requests.json"


def _load_pending() -> dict:
    """Load pending requests from JSON file."""
    if not PENDING_FILE.exists():
        return {}
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # File is empty
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        return {}


def _save_pending(data: dict) -> None:
    """Save pending requests to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_request_id() -> str:
    """Generate a unique request ID based on current timestamp."""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    pending = _load_pending()

    # Count requests for today
    today_count = sum(1 for rid in pending.keys() if date_str in rid)
    sequence = str(today_count + 1).zfill(2)

    return f"NP-{date_str}{sequence}"


def save_request(request_id: str, data: dict) -> None:
    """Save a new pending request."""
    pending = _load_pending()
    pending[request_id] = {
        **data,
        "created_at": datetime.now().isoformat(),
        "reminder_sent": False
    }
    _save_pending(pending)


def get_request(request_id: str) -> Optional[dict]:
    """Get a pending request by ID."""
    pending = _load_pending()
    return pending.get(request_id)


def get_all_requests() -> dict:
    """Get all pending requests."""
    return _load_pending()


async def get_all_requests_with_fallback() -> dict:
    """
    Get all pending requests with fallback to Google Sheets.
    If local file is empty, restores from Google Sheets backup.
    """
    from bot.services.pending_backup import load_pending_with_fallback
    return await load_pending_with_fallback()


def get_requests_by_employee(employee_telegram: str) -> dict:
    """Get all pending requests for an employee."""
    pending = _load_pending()
    return {
        rid: data for rid, data in pending.items()
        if data.get("employee_telegram") == employee_telegram
    }


def get_requests_older_than(hours: int = 24) -> dict:
    """Get pending requests older than specified hours that haven't been reminded."""
    pending = _load_pending()
    now = datetime.now()
    result = {}

    for rid, data in pending.items():
        if data.get("reminder_sent"):
            continue
        created_at = datetime.fromisoformat(data.get("created_at", now.isoformat()))
        age_hours = (now - created_at).total_seconds() / 3600
        if age_hours >= hours:
            result[rid] = data

    return result


def mark_reminder_sent(request_id: str) -> None:
    """Mark a request as having been reminded."""
    pending = _load_pending()
    if request_id in pending:
        pending[request_id]["reminder_sent"] = True
        _save_pending(pending)


def update_request(request_id: str, updates: dict) -> None:
    """Update a pending request."""
    pending = _load_pending()
    if request_id in pending:
        pending[request_id].update(updates)
        _save_pending(pending)


def delete_request(request_id: str) -> Optional[dict]:
    """Delete a pending request and return it."""
    pending = _load_pending()
    if request_id in pending:
        data = pending.pop(request_id)
        _save_pending(pending)
        return data
    return None
