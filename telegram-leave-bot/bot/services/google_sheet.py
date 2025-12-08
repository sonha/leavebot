import gspread
from bot.config import SPREADSHEET_ID, GOOGLE_CREDENTIALS_FILE
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os
import asyncio

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

# Cache file path
EMPLOYEES_FILE = 'data/employees.json'

# Cache for employee data (1 day expiration for in-memory, but file persists)
_employee_cache = None
_cache_time = None
CACHE_DURATION = timedelta(days=1)

def clear_employee_cache():
    """Manually clear the employee cache."""
    global _employee_cache, _cache_time
    _employee_cache = None
    _cache_time = None
    
# ... (imports remain)

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

# ... (get_all_employees_cached remains same)

# ... (get_employee_by_telegram, get_all_employees, get_manager_telegram remain same as they call async or cached functions)

async def approve_leave(request_data: dict) -> bool:
    """
    Append approved leave to 'Raw' sheet.
    """
    try:
        # Prepare row data (same logic as before)
        row = [
            '=ROW()-1',
            request_data.get('leave_type', ''),
            request_data.get('employee_email', ''),
            request_data.get('manager_email', ''),
            request_data.get('reason', ''),
            'Submitted via Telegram Bot',
            '', # Leave minutes
            request_data.get('start_date', ''),
            request_data.get('start_shift', ''),
            request_data.get('end_date', ''),
            request_data.get('end_shift', ''),
            request_data.get('created_at', ''),
            request_data.get('approved_by', ''), 
            request_data.get('approved_at', ''),
            'No'
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

