"""
Test script for pending requests backup and restore functionality.
"""
import asyncio
from bot.services.pending_backup import (
    backup_pending_requests_to_sheet,
    restore_pending_requests_from_sheet,
    load_pending_with_fallback
)
from bot.services.pending_store import get_all_requests


async def test_backup():
    """Test backing up pending requests to Google Sheets."""
    print("=" * 60)
    print("TEST 1: Backup pending requests to Google Sheets")
    print("=" * 60)

    # Get current pending requests
    pending = get_all_requests()
    print(f"\nCurrent pending requests count: {len(pending)}")

    # Backup to Google Sheets
    success = await backup_pending_requests_to_sheet()

    if success:
        print("\n✅ Backup successful!")
    else:
        print("\n❌ Backup failed!")

    return success


async def test_restore():
    """Test restoring pending requests from Google Sheets."""
    print("\n" + "=" * 60)
    print("TEST 2: Restore pending requests from Google Sheets")
    print("=" * 60)

    # Restore from Google Sheets
    restored = await restore_pending_requests_from_sheet()

    print(f"\nRestored pending requests count: {len(restored)}")

    if restored:
        print("\n✅ Restore successful!")
        print("\nSample restored request:")
        first_key = list(restored.keys())[0]
        print(f"Request ID: {first_key}")
        for key, value in restored[first_key].items():
            print(f"  {key}: {value}")
    else:
        print("\n❌ Restore failed or no data found!")

    return len(restored) > 0


async def test_fallback():
    """Test the fallback loading mechanism."""
    print("\n" + "=" * 60)
    print("TEST 3: Test fallback loading mechanism")
    print("=" * 60)

    # Test load with fallback
    pending = await load_pending_with_fallback()

    print(f"\nLoaded pending requests count: {len(pending)}")

    if pending:
        print("\n✅ Fallback loading successful!")
    else:
        print("\n⚠️  No pending requests loaded (this is OK if both sources are empty)")

    return True


async def main():
    """Run all tests."""
    print("\n🧪 TESTING PENDING REQUESTS BACKUP SYSTEM\n")

    try:
        # Test 1: Backup
        backup_success = await test_backup()

        # Test 2: Restore
        restore_success = await test_restore()

        # Test 3: Fallback
        fallback_success = await test_fallback()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Backup test: {'✅ PASSED' if backup_success else '❌ FAILED'}")
        print(f"Restore test: {'✅ PASSED' if restore_success else '❌ FAILED'}")
        print(f"Fallback test: {'✅ PASSED' if fallback_success else '❌ FAILED'}")

        if backup_success and restore_success and fallback_success:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed. Please check the logs above.")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
