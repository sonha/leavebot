import gspread
from bot.config import SPREADSHEET_ID, GOOGLE_CREDENTIALS_FILE
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os
import asyncio

# Cache file path
EMPLOYEES_FILE = 'data/employees.json'

# Cache for employee data (1 day expiration)
_employee_cache = None
_cache_time = None
CACHE_DURATION = timedelta(days=1)

class GoogleSheetService:
    _instance = None
    _client = None
    _spreadsheet = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_client(self):
        if self._client is None:
            self._client = gspread.service_account(filename=GOOGLE_CREDENTIALS_FILE)
        return self._client

    def _get_spreadsheet(self):
        if self._spreadsheet is None:
            client = self._get_client()
            self._spreadsheet = client.open_by_key(SPREADSHEET_ID)
        return self._spreadsheet

    def get_sheet(self, sheet_name: str):
        return self._get_spreadsheet().worksheet(sheet_name)

def _ensure_data_dir():
    """Ensure data directory exists."""
    os.makedirs(os.path.dirname(EMPLOYEES_FILE), exist_ok=True)

def _save_employees_to_file(employees: list):
    """Save employees to JSON file."""
    try:
        _ensure_data_dir()
        with open(EMPLOYEES_FILE, 'w', encoding='utf-8') as f:
            json.dump(employees, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(employees)} employees to {EMPLOYEES_FILE}")
    except Exception as e:
        print(f"Error saving employees to file: {e}")

def _load_employees_from_file() -> Optional[list]:
    """Load employees from JSON file."""
    if not os.path.exists(EMPLOYEES_FILE):
        return None
    
    try:
        with open(EMPLOYEES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading employees from file: {e}")
        return None

def clear_employee_cache():
    """Manually clear the employee cache and delete local file."""
    global _employee_cache, _cache_time
    _employee_cache = None
    _cache_time = None
    
    # Delete local file to force refresh from Sheet
    if os.path.exists(EMPLOYEES_FILE):
        try:
            os.remove(EMPLOYEES_FILE)
            print("Deleted local employee cache file.")
        except OSError as e:
            print(f"Error deleting cache file: {e}")

async def _fetch_all_employees_from_sheet() -> list:
    """Internal function to fetch employees from Google Sheets (no cache)."""
    try:
        def _fetch():
            service = GoogleSheetService.get_instance()
            sheet = service.get_sheet('Nhân sự')
            return sheet.get_all_values()

        # Run blocking call in thread
        records = await asyncio.to_thread(_fetch)

        if not records or len(records) < 2:
            return []

        headers = records[0]
        header_map = {h.lower(): i for i, h in enumerate(headers)}

        # Find telegram column
        telegram_idx = -1
        for h, idx in header_map.items():
            if 'telegram' in h:
                telegram_idx = idx
                break
        if telegram_idx == -1:
            telegram_idx = 8  # Fallback to column I

        employees = []
        for row in records[1:]:
            if len(row) > max(telegram_idx, 9):
                employees.append({
                    "name": row[1],
                    "email": row[3],
                    "telegram": row[telegram_idx] if len(row) > telegram_idx else "",
                    "manager_email": row[9] if len(row) > 9 else "",
                    "is_official": row[4] == 'Yes' if len(row) > 4 else False,
                    "is_working": row[5] == 'Yes' if len(row) > 5 else False
                })
        return employees
    except Exception as e:
        print(f"Error fetching employees from sheet: {e}")
        return []

async def get_all_employees_cached() -> list:
    """Get all employees with file-based persistence."""
    global _employee_cache, _cache_time

    now = datetime.now()

    # 1. Return in-memory cache if valid
    if _employee_cache is not None and _cache_time is not None:
        if (now - _cache_time) < CACHE_DURATION:
            return _employee_cache

    # 2. Try loading from local file (if not in memory)
    file_data = await asyncio.to_thread(_load_employees_from_file)
    if file_data and os.path.exists(EMPLOYEES_FILE): # Double check file exists to respect manual clear
         # Logic check: if we just cleared the file, we shouldn't load it. 
         # _load_employees_from_file checks existence.
         print("Loaded employees from local file.")
         _employee_cache = file_data
         _cache_time = now
         return _employee_cache

    # 3. Fetch fresh data from Google Sheets (fallback)
    print("Fetching fresh employee data from Google Sheets...")
    _employee_cache = await _fetch_all_employees_from_sheet()
    _cache_time = now
    
    # 4. Save to local file
    if _employee_cache:
        await asyncio.to_thread(_save_employees_to_file, _employee_cache)
        
    print(f"Cached {len(_employee_cache)} employees")
    return _employee_cache

async def get_employee_by_telegram(telegram_username: str) -> Optional[dict]:
    """
    Get employee info by Telegram username (uses cached data).
    """
    try:
        employees = await get_all_employees_cached()

        for emp in employees:
            emp_telegram = emp.get("telegram", "").strip().lower()
            if emp_telegram == telegram_username.strip().lower():
                return emp
        return None
    except Exception as e:
        print(f"Error getting employee by telegram: {e}")
        return None

async def get_all_employees() -> list:
    """Get all working employees (uses cached data)."""
    try:
        all_employees = await get_all_employees_cached()
        # Filter only working employees
        return [emp for emp in all_employees if emp.get("is_working", False)]
    except Exception as e:
        print(f"Error getting employees: {e}")
        return []

async def get_manager_telegram(manager_email: str) -> Optional[str]:
    """Find manager telegram by email (uses cached data)."""
    try:
        employees = await get_all_employees_cached()
        for emp in employees:
            if emp.get("email") == manager_email:
                return emp.get("telegram")
        return None
    except Exception as e:
        print(f"Error getting manager telegram: {e}")
        return None

async def approve_leave(request_data: dict) -> bool:
    """
    Append approved leave to 'Raw' sheet.
    """
    try:
        # Get leave_minutes for Đi muộn/Về sớm, otherwise leave blank
        leave_type = request_data.get('leave_type', '')
        leave_minutes = ''
        if leave_type in ['Đi muộn', 'Về sớm']:
            leave_minutes = request_data.get('leave_minutes', '')

        # Prepare row data
        # Columns: A=blank, B=Loại, C=Email, D=Quản lý, E=blank, F=Lý do, G=Số phút, H-K=Dates/Shifts, L-N=Timestamps, O=Revoked
        row = [
            '',                                      # A: blank
            leave_type,                              # B: Loại Hình
            request_data.get('employee_email', ''),  # C: Người Gửi
            request_data.get('manager_email', ''),   # D: Quản Lý
            '',                                      # E: blank
            request_data.get('reason', ''),          # F: Lý Do
            leave_minutes,                           # G: Số phút đi muộn/về sớm
            request_data.get('start_date', ''),      # H: Thời gian bắt đầu
            request_data.get('start_shift', ''),     # I: Ca bắt đầu
            request_data.get('end_date', ''),        # J: Thời gian kết thúc
            request_data.get('end_shift', ''),       # K: Ca kết thúc
            request_data.get('created_at', ''),      # L: Tạo lúc
            request_data.get('approved_by', ''),     # M: Duyệt bởi
            request_data.get('approved_at', ''),     # N: Duyệt lúc
            'No'                                     # O: Revoked
        ]

        def _append():
            service = GoogleSheetService.get_instance()
            sheet = service.get_sheet('Raw')
            sheet.append_row(row, value_input_option='USER_ENTERED')

        # Run blocking call in thread
        await asyncio.to_thread(_append)
        return True
    except Exception as e:
        print(f"Error approving leave: {e}")
        return False
