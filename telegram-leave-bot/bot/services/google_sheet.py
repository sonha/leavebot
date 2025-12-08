import gspread
from bot.config import SPREADSHEET_ID, GOOGLE_CREDENTIALS_FILE
from typing import Optional, List, Dict, Any
from datetime import datetime

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

# Helper functions that match the previous interface
async def get_employee_by_telegram(telegram_username: str) -> Optional[dict]:
    """
    Get employee info by Telegram username from 'Nhân sự' sheet.
    """
    try:
        service = GoogleSheetService.get_instance()
        sheet = service.get_sheet('Nhân sự')
        
        # Get all records
        records = sheet.get_all_values()
        headers = records[0]
        
        # Find column indices (using lowered headers for safety)
        header_map = {h.lower(): i for i, h in enumerate(headers)}
        
        telegram_idx = -1
        for h, idx in header_map.items():
            if 'telegram' in h:
                telegram_idx = idx
                break
        
        if telegram_idx == -1: 
            # Fallback to column I (index 8) if header not found
            telegram_idx = 8

        # Iterate through rows
        for row in records[1:]:
            if len(row) <= telegram_idx: continue
            
            row_telegram = row[telegram_idx]
            if str(row_telegram).strip().lower() == telegram_username.strip().lower():
                # Map row to employee object
                # Assuming standard structure: 
                # B=Name(1), D=Email(3), E=Official(4), F=Working(5), Manager(Col J/9)
                return {
                    "name": row[1],
                    "email": row[3],
                    "telegram": row_telegram,
                    "manager_email": row[9] if len(row) > 9 else "",
                    "is_official": row[4] == 'Yes',
                    "is_working": row[5] == 'Yes'
                }
        return None
    except Exception as e:
        print(f"Error getting employee by telegram: {e}")
        return None

async def get_all_employees() -> list:
    """Get all working employees."""
    try:
        service = GoogleSheetService.get_instance()
        sheet = service.get_sheet('Nhân sự')
        records = sheet.get_all_values()
        
        employees = []
        # Basic parsing similar to above
        for row in records[1:]:
            if len(row) > 5 and row[5] == 'Yes': # Working = Yes
                employees.append({
                    "name": row[1],
                    "email": row[3],
                    "telegram": row[8] if len(row) > 8 else "", # Plain guesswork on column I
                    "manager_email": row[9] if len(row) > 9 else ""
                })
        return employees
    except Exception as e:
        print(f"Error getting employees: {e}")
        return []

async def get_manager_telegram(manager_email: str) -> Optional[str]:
    """Find manager telegram by email locally from fetched list."""
    employees = await get_all_employees()
    for emp in employees:
        if emp.get("email") == manager_email:
            return emp.get("telegram")
    return None

async def approve_leave(request_data: dict) -> bool:
    """
    Append approved leave to 'Raw' sheet.
    """
    try:
        service = GoogleSheetService.get_instance()
        sheet = service.get_sheet('Raw')
        
        # Prepare row data
        # Columns: [STT, Loại, Người Gửi, Quản Lý, Lý Do, Mô tả, ..., CreatedAt, ApprovedBy, ApprovedAt, Revoked]
        # A: STT -> formula =ROW()-1
        # B: Type -> request_data['leave_type']
        # C: Requester -> request_data['employee_email']
        # D: Manager -> request_data['manager_email']
        # E: Reason -> request_data['reason']
        # F: Desc -> "Submitted via Telegram Bot"
        # G: LeaveMinutes -> ""
        # H: StartDate -> request_data['start_date']
        # I: StartShift -> request_data['start_shift']
        # J: EndDate -> request_data['end_date']
        # K: EndShift -> request_data['end_shift']
        # L: CreatedAt -> request_data['created_at']
        # M: ApprovedBy -> request_data['approved_by']
        # N: ApprovedAt -> request_data['approved_at']
        # O: Revoked -> "No"

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
            request_data.get('approved_by', ''), # This field was missing in original payload example but required logic
            request_data.get('approved_at', ''),
            'No'
        ]

        sheet.append_row(row, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        print(f"Error approving leave: {e}")
        return False
