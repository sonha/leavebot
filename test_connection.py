import asyncio
import os
from bot.services.google_sheet import GoogleSheetService, approve_leave

async def main():
    print("Testing Google Sheets Connection...")
    
    # 1. Test Read Access
    try:
        service = GoogleSheetService.get_instance()
        sheet_title = service._get_spreadsheet().title
        print(f"✅ Connection Successful! Connected to Sheet: '{sheet_title}'")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        import traceback
        print("\nFull error details:")
        traceback.print_exc()
        return

    # 2. Test Write Access (Append to Raw)
    print("\nTesting Write Access (Appending to 'Raw')...")
    test_data = {
        "leave_type": "TEST_ENTRY",
        "employee_email": "test_bot@nerdlabs.tech",
        "manager_email": "admin@nerdlabs.tech",
        "reason": "Connection Verification",
        "start_date": "2025-01-01",
        "start_shift": "Cả ngày",
        "end_date": "2025-01-01", 
        "end_shift": "Cả ngày",
        "created_at": "2025-01-01",
        "approved_by": "System Test",
        "approved_at": "2025-01-01"
    }

    success = await approve_leave(test_data)
    if success:
        print("✅ Write Successful! Check the 'Raw' sheet for a specific row.")
    else:
        print("❌ Write Failed.")

if __name__ == "__main__":
    asyncio.run(main())
