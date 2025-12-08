import asyncio
from bot.services.google_sheet import GoogleSheetService

async def main():
    service = GoogleSheetService.get_instance()
    ss = service._get_spreadsheet()
    
    print(f"Spreadsheet Title: '{ss.title}'")
    print(f"Spreadsheet ID: {ss.id}")
    
    sheets = ss.worksheets()
    print("Available Worksheets:")
    for s in sheets:
        print(f" - '{s.title}' (Rows: {s.row_count})")

    try:
        raw_sheet = ss.worksheet('Raw')
        print(f"\nChecking 'Raw' sheet...")
        
        all_values = raw_sheet.get_all_values()
        total_rows = len(all_values)
        print(f"Total rows with data: {total_rows}")
        
        if total_rows > 0:
            print("Last 3 rows:")
            for i in range(max(0, total_rows - 3), total_rows):
                print(f"Row {i+1}: {all_values[i]}")
        else:
            print("Sheet appears empty.")
            
        # Search for TEST_ENTRY
        print("\nSearching for 'TEST_ENTRY'...")
        found = False
        for i, row in enumerate(all_values):
            if "TEST_ENTRY" in row:
                print(f"✅ FOUND at Row {i+1}: {row}")
                found = True
                break
        
        if not found:
            print("❌ 'TEST_ENTRY' NOT FOUND in the entire sheet.")
            
    except Exception as e:
        print(f"Error accessing 'Raw' sheet: {e}")

if __name__ == "__main__":
    asyncio.run(main())
