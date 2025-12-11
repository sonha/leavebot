import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Sheets Config
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# Telegram Group ID for approvals
APPROVAL_GROUP_ID = int(os.getenv("APPROVAL_GROUP_ID", "0"))

# Telegram Topic ID for approvals (for forum groups)
APPROVAL_TOPIC_ID = int(os.getenv("APPROVAL_TOPIC_ID", "0")) or None

# Admin ID for error notifications
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) or None

# Validate required config
def validate_config():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    if not SPREADSHEET_ID:
        raise ValueError("SPREADSHEET_ID is required")
    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        raise ValueError(f"Credentials file not found at: {GOOGLE_CREDENTIALS_FILE}")
    if not APPROVAL_GROUP_ID:
        raise ValueError("APPROVAL_GROUP_ID is required")
