# Telegram Leave Request Bot

A Telegram bot for managing employee leave requests with Google Sheets integration.

## Features

- **User Registration**: Automatic validation against employee database
- **Interactive Leave Requests**: Step-by-step conversation flow with calendar picker
- **Manager Approvals**: Real-time approval/rejection via Telegram group
- **Google Sheets Integration**: Reads employee data and writes approved leaves
- **Automated Reminders**: Hourly checks for pending requests older than 24 hours
- **Shift Support**: Morning, afternoon, or full-day leave options

## Prerequisites

- Python 3.8 or higher (tested with Python 3.9.6)
- Google Sheets with "Nhân sự" (employee) and "Raw" (leave records) sheets
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Google service account credentials

## Installation

1. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Configure environment variables**:

   Edit `.env` file with your values:
   ```
   BOT_TOKEN=your_bot_token_here
   SPREADSHEET_ID=your_google_sheet_id
   APPROVAL_GROUP_ID=your_telegram_group_id
   GOOGLE_CREDENTIALS_FILE=credentials.json
   ```

3. **Set up Google Sheets credentials**:
   - Place your Google service account JSON file as `credentials.json` in the project root
   - Ensure the service account has edit access to your spreadsheet

## Running the Bot

### Option 1: Using startup script (recommended)
```bash
./start_bot.sh
```

### Option 2: Direct command
```bash
python3 -m bot.main
```

### Option 3: Run in background with screen
```bash
screen -S telegram-bot
python3 -m bot.main
# Press Ctrl+A, then D to detach
# Reattach later: screen -r telegram-bot
```

### Option 4: Run in background with nohup
```bash
nohup python3 -m bot.main > bot.log 2>&1 &
# Check if running: ps aux | grep "bot.main"
# Stop: pkill -f "bot.main"
```

## Usage

### For Employees

1. **Start the bot**: Send `/start` to the bot
   - Bot will validate your Telegram username against the "Nhân sự" sheet

2. **Request leave**: Send `/nghiphep`
   - Select leave type
   - Choose start date using interactive calendar
   - Select single day or date range
   - Choose shift (morning/afternoon/full day)
   - Enter reason for leave
   - Review and confirm

3. **Receive confirmation**: Bot sends notification when manager approves/rejects

### For Managers

1. **Receive requests**: Leave requests appear in the approval group
2. **Review details**: See employee name, dates, shifts, and reason
3. **Take action**: Click "Phê duyệt" (Approve) or "Từ chối" (Reject)
4. **Only assigned managers** can approve their team members' requests

## Google Sheets Structure

### "Nhân sự" Sheet (Employee Data)
Required columns:
- Name
- Email
- Telegram username
- Manager email
- Working status

### "Raw" Sheet (Leave Records)
Columns written by bot:
- STT (auto-generated)
- Loại Hình (leave type)
- Người Gửi (requester)
- Quản Lý (manager)
- Lý Do (reason)
- Mô tả (description)
- Số phút (minutes)
- Thời gian bắt đầu (start date)
- Ca bắt đầu (start shift)
- Thời gian kết thúc (end date)
- Ca kết thúc (end shift)
- Tạo lúc (created at)
- Duyệt bởi (approved by)
- Duyệt lúc (approved at)
- Revoked

## Architecture

```
telegram-leave-bot/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── handlers/            # Command handlers
│   ├── keyboards/           # UI components
│   ├── services/            # Google Sheets & reminders
│   └── utils/               # Utilities
├── data/
│   └── pending_requests.json  # Local storage
├── credentials.json         # Google credentials
├── .env                     # Environment config
├── requirements.txt         # Dependencies
├── start_bot.sh            # Startup script
└── README.md               # This file
```

## Troubleshooting

### Bot doesn't start
- Check `.env` file has all required variables
- Verify `credentials.json` exists and is valid
- Ensure Python 3.8+ is installed

### User not found
- Verify user has Telegram username set in "Nhân sự" sheet
- Check username format (no @ symbol in sheet)

### Approval buttons don't work
- Ensure bot is added to approval group
- Make bot an admin in the group
- Verify APPROVAL_GROUP_ID is correct (negative number)

### Google Sheets errors
- Confirm service account has edit access to spreadsheet
- Check SPREADSHEET_ID in .env matches your sheet
- Verify sheet names are exactly "Nhân sự" and "Raw"

## Stopping the Bot

- **Foreground mode**: Press `Ctrl+C`
- **Background mode**: `pkill -f "bot.main"`
- **Screen mode**: Reattach with `screen -r telegram-bot`, then `Ctrl+C`

## Notes

- Bot uses long-polling (no webhook needed)
- Computer must stay on and connected to internet
- Average memory usage: 50-100MB
- Pending requests persist in `data/pending_requests.json`
- Reminder scheduler runs every hour
- Logs appear in console (redirect to file if needed)

## Support

For issues or questions, check the logs and verify configuration settings.
