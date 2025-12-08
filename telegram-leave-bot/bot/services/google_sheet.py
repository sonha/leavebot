import httpx
from typing import Optional
from bot.config import SHEET_API_URL


async def _call_api(action: str, data: dict = None) -> dict:
    """Call Google Apps Script API."""
    payload = {"action": action, **(data or {})}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            SHEET_API_URL,
            json=payload,
            timeout=30.0,
            follow_redirects=True
        )
        response.raise_for_status()
        return response.json()


async def get_employee_by_telegram(telegram_username: str) -> Optional[dict]:
    """
    Get employee info by Telegram username.

    Returns:
        {
            "email": "jones@nerdlabs.tech",
            "name": "Jones",
            "telegram": "@jones",
            "manager_email": "boss@nerdlabs.tech",
            "is_official": True,
            "is_working": True
        }
        or None if not found
    """
    try:
        result = await _call_api("get_employee_by_telegram", {
            "telegram_username": telegram_username
        })
        if result.get("success") and result.get("employee"):
            return result["employee"]
        return None
    except Exception as e:
        print(f"Error getting employee by telegram: {e}")
        return None


async def get_all_employees() -> list:
    """
    Get all employees with their Telegram usernames.
    Used for manager lookup.

    Returns:
        [
            {
                "email": "jones@nerdlabs.tech",
                "name": "Jones",
                "telegram": "@jones",
                "manager_email": "boss@nerdlabs.tech"
            },
            ...
        ]
    """
    try:
        result = await _call_api("get_employees")
        if result.get("success"):
            return result.get("employees", [])
        return []
    except Exception as e:
        print(f"Error getting employees: {e}")
        return []


async def get_manager_telegram(manager_email: str) -> Optional[str]:
    """
    Get manager's Telegram username by their email.
    Searches all employees to find the manager's Telegram.
    """
    employees = await get_all_employees()
    for emp in employees:
        if emp.get("email") == manager_email:
            return emp.get("telegram")
    return None


async def approve_leave(request_data: dict) -> bool:
    """
    Write approved leave request to Raw sheet.

    Args:
        request_data: {
            "employee_email": "jones@nerdlabs.tech",
            "manager_email": "boss@nerdlabs.tech",
            "leave_type": "Nghỉ phép",
            "start_date": "2025-12-15",
            "start_shift": "Cả ngày",
            "end_date": "2025-12-17",
            "end_shift": "Cả ngày",
            "reason": "Việc gia đình",
            "created_at": "2025-12-08T10:30:00",
            "approved_at": "2025-12-08T11:00:00"
        }

    Returns:
        True if successful, False otherwise
    """
    try:
        result = await _call_api("approve_leave", request_data)
        return result.get("success", False)
    except Exception as e:
        print(f"Error approving leave: {e}")
        return False
