"""
Service for backing up and restoring pending requests to/from Google Sheets.
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
from bot.services.google_sheet import GoogleSheetService
from bot.services.pending_store import _load_pending, _save_pending, PENDING_FILE


async def backup_pending_requests_to_sheet() -> bool:
    """
    Backup all pending requests to the 'Pending Requests' sheet in Google Sheets.
    Each request is saved as a row with its data.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"[{datetime.now()}] Starting pending requests backup to Google Sheets...")

        # Load current pending requests
        pending = _load_pending()

        def _backup():
            service = GoogleSheetService.get_instance()
            sheet = service.get_sheet('Pending Requests')

            # Clear existing data (except header)
            sheet.clear()

            # Set headers
            headers = [
                'Request ID',
                'Employee Email',
                'Employee Telegram',
                'Employee Name',
                'Manager Email',
                'Manager Telegram',
                'Leave Type',
                'Start Date',
                'Start Shift',
                'End Date',
                'End Shift',
                'Leave Minutes',
                'Reason',
                'User Chat ID',
                'Created At',
                'Reminder Sent',
                'Message ID'
            ]
            sheet.append_row(headers, value_input_option='USER_ENTERED')

            # Add each pending request as a row
            for request_id, data in pending.items():
                row = [
                    request_id,
                    data.get('employee_email', ''),
                    data.get('employee_telegram', ''),
                    data.get('employee_name', ''),
                    data.get('manager_email', ''),
                    data.get('manager_telegram', ''),
                    data.get('leave_type', ''),
                    data.get('start_date', ''),
                    data.get('start_shift', ''),
                    data.get('end_date', ''),
                    data.get('end_shift', ''),
                    str(data.get('leave_minutes', '')) if data.get('leave_minutes') is not None else '',
                    data.get('reason', ''),
                    str(data.get('user_chat_id', '')),
                    data.get('created_at', ''),
                    str(data.get('reminder_sent', False)),
                    str(data.get('message_id', '')) if data.get('message_id') else ''
                ]
                sheet.append_row(row, value_input_option='USER_ENTERED')

        # Run blocking call in thread
        await asyncio.to_thread(_backup)

        print(f"[{datetime.now()}] Successfully backed up {len(pending)} pending requests to Google Sheets")
        return True

    except Exception as e:
        print(f"[{datetime.now()}] Error backing up pending requests: {e}")
        return False


async def restore_pending_requests_from_sheet() -> Dict:
    """
    Restore pending requests from the 'Pending Requests' sheet in Google Sheets.
    Returns the restored pending requests as a dictionary.
    """
    try:
        print(f"[{datetime.now()}] Restoring pending requests from Google Sheets...")

        def _restore():
            service = GoogleSheetService.get_instance()
            sheet = service.get_sheet('Pending Requests')
            return sheet.get_all_values()

        # Run blocking call in thread
        records = await asyncio.to_thread(_restore)

        if not records or len(records) < 2:
            print(f"[{datetime.now()}] No data found in Pending Requests sheet")
            return {}

        # Skip header row
        headers = records[0]

        # Build pending requests dictionary
        pending = {}
        for row in records[1:]:
            if len(row) < 15:  # Minimum required columns
                continue

            request_id = row[0]
            if not request_id:
                continue

            data = {
                'employee_email': row[1] if len(row) > 1 else '',
                'employee_telegram': row[2] if len(row) > 2 else '',
                'employee_name': row[3] if len(row) > 3 else '',
                'manager_email': row[4] if len(row) > 4 else '',
                'manager_telegram': row[5] if len(row) > 5 else '',
                'leave_type': row[6] if len(row) > 6 else '',
                'start_date': row[7] if len(row) > 7 else '',
                'start_shift': row[8] if len(row) > 8 else '',
                'end_date': row[9] if len(row) > 9 else None if (len(row) <= 9 or row[9] == '') else row[9],
                'end_shift': row[10] if len(row) > 10 else None if (len(row) <= 10 or row[10] == '') else row[10],
                'leave_minutes': int(row[11]) if len(row) > 11 and row[11] and row[11].isdigit() else None,
                'reason': row[12] if len(row) > 12 else '',
                'user_chat_id': int(row[13]) if len(row) > 13 and row[13] and (row[13].isdigit() or (row[13].startswith('-') and row[13][1:].isdigit())) else 0,
                'created_at': row[14] if len(row) > 14 else '',
                'reminder_sent': row[15].lower() == 'true' if len(row) > 15 else False,
            }

            # Add message_id if present
            if len(row) > 16 and row[16]:
                try:
                    data['message_id'] = int(row[16])
                except ValueError:
                    pass

            pending[request_id] = data

        print(f"[{datetime.now()}] Successfully restored {len(pending)} pending requests from Google Sheets")
        return pending

    except Exception as e:
        print(f"[{datetime.now()}] Error restoring pending requests: {e}")
        return {}


async def load_pending_with_fallback() -> Dict:
    """
    Load pending requests with fallback logic:
    1. Try to load from local JSON file
    2. If file is empty or doesn't exist, load from Google Sheets
    3. Save to local file if loaded from Sheets

    Returns the pending requests dictionary.
    """
    try:
        # Check if local file exists and has content
        if PENDING_FILE.exists():
            pending = _load_pending()
            if pending:  # File exists and has data
                print(f"[{datetime.now()}] Loaded {len(pending)} pending requests from local file")
                return pending

        # File is empty or doesn't exist, try to restore from Google Sheets
        print(f"[{datetime.now()}] Local file empty or missing, restoring from Google Sheets...")
        pending = await restore_pending_requests_from_sheet()

        if pending:
            # Save restored data to local file
            _save_pending(pending)
            print(f"[{datetime.now()}] Saved restored data to local file")

        return pending

    except Exception as e:
        print(f"[{datetime.now()}] Error in load_pending_with_fallback: {e}")
        return {}
