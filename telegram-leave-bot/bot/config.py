import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Apps Script Web App URL
SHEET_API_URL = os.getenv("SHEET_API_URL")

# Telegram Group ID for approvals
APPROVAL_GROUP_ID = int(os.getenv("APPROVAL_GROUP_ID", "0"))

# Validate required config
def validate_config():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    if not SHEET_API_URL:
        raise ValueError("SHEET_API_URL is required")
    if not APPROVAL_GROUP_ID:
        raise ValueError("APPROVAL_GROUP_ID is required")
