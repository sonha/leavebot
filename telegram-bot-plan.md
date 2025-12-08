# Telegram Leave Request Bot - Design Plan

## Overview
A Python Telegram bot that allows employees to submit leave requests through an interactive conversation, with manager approval via inline buttons in a group chat.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram Bot   │────▶│  Python Server  │────▶│ Google Apps     │
│  (User Chat)    │     │  (Bot Logic)    │     │ Script API      │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
┌─────────────────┐              │              ┌────────▼────────┐
│  Telegram Group │◀─────────────┘              │  Google Sheet   │
│  (Approvals)    │                             │  (Raw + Data)   │
└─────────────────┘                             └─────────────────┘
```

---

## Data Storage

### Google Sheets (Same Spreadsheet as existing)
The bot will use the **existing Google Spreadsheet** that contains "Raw", "Nhân sự", "Chấm công" sheets.

**Sheet: "Nhân sự"** (Existing - admin manages all employee data)
Admin adds 2 new columns:
| ... existing columns ... | Telegram Username | Manager Email |
|--------------------------|-------------------|---------------|
| jones@nerdlabs.tech | @jones | boss@nerdlabs.tech |
| boss@nerdlabs.tech | @boss | ceo@nerdlabs.tech |

- **Telegram Username:** Bot matches user's Telegram @ to identify employee
- **Manager Email:** Bot looks up this email in same sheet to find manager's Telegram @

**Sheet: "Raw"** (Existing - where approved leave requests are stored)
Bot writes approved requests here with all 15 columns as defined in existing structure.
- Only written AFTER manager approves
- Rejected/ignored requests are NOT written here

**Local File: `pending_requests.json`** (On Python server)
Stores pending requests before approval:
```json
{
  "NP-2025120801": {
    "employee_email": "jones@nerdlabs.tech",
    "employee_telegram": "@jones",
    "manager_email": "boss@nerdlabs.tech",
    "manager_telegram": "@boss",
    "leave_type": "Nghỉ phép",
    "start_date": "2025-12-15",
    "start_shift": "Cả ngày",
    "end_date": "2025-12-17",
    "end_shift": "Cả ngày",
    "reason": "Việc gia đình",
    "created_at": "2025-12-08T10:30:00",
    "message_id": 12345,
    "reminder_sent": false
  }
}
```

---

## Bot Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/start` | Welcome message + auto-check registration | All |
| `/nghiphep` | Start leave request flow | Registered users (auto-detected) |
| `/trangthai` | Check pending requests | Registered users |
| `/huy <request_id>` | Cancel pending request | Registered users |

**No `/dangky` command** - Registration is automatic:
- Bot reads user's Telegram username
- Searches "Nhân sự" sheet for matching Telegram Username column
- If found → user is registered
- If not found → "❌ Telegram của bạn chưa được đăng ký. Vui lòng liên hệ HR."

---

## User Flows

### Flow 1: Auto-Registration Check
```
User: /start or /nghiphep

Bot checks "Nhân sự" sheet:
- Reads user's Telegram username (e.g., @jones)
- Searches for row where Telegram Username = @jones
- If found → User identified as jones@nerdlabs.tech

Bot: ✅ Xin chào Jones!
     Email: jones@nerdlabs.tech
     Sử dụng /nghiphep để xin nghỉ phép.
```

If Telegram username not found in "Nhân sự" sheet:
```
Bot: ❌ Telegram của bạn chưa được đăng ký trong hệ thống.
     Vui lòng liên hệ HR để được thêm vào danh sách nhân sự.
```

### Flow 2: Leave Request (Interactive)
```
User: /nghiphep

Bot: 📋 CHỌN LOẠI NGHỈ
     [WFH] [Nghỉ phép] [Nghỉ không lương]

User: [Nghỉ phép]

Bot: 📅 CHỌN NGÀY BẮT ĐẦU
     [◀ Tháng 12 2025 ▶]
     [CN] [T2] [T3] [T4] [T5] [T6] [T7]
     [ 1] [ 2] [ 3] [ 4] [ 5] [ 6] [ 7]
     [ 8] [ 9] [10] [11] [12] [13] [14]
     [15] [16] [17] [18] [19] [20] [21]
     ...
     [Chỉ 1 ngày] [Chọn khoảng ngày]

User: [15] then [Chọn khoảng ngày]

Bot: 📅 CHỌN NGÀY KẾT THÚC
     (calendar...)

User: [17]

Bot: ⏰ CHỌN CA LÀM VIỆC
     Ngày bắt đầu (15/12):
     [Sáng] [Chiều] [Cả ngày]

User: [Cả ngày]

Bot: ⏰ CHỌN CA KẾT THÚC
     Ngày kết thúc (17/12):
     [Sáng] [Chiều] [Cả ngày]

User: [Cả ngày]

Bot: 📝 NHẬP LÝ DO
     Vui lòng nhập lý do nghỉ:

User: Việc gia đình

Bot: 📋 XÁC NHẬN THÔNG TIN
     ━━━━━━━━━━━━━━━━━━━━
     Loại: Nghỉ phép
     Từ: 15/12/2025 (Cả ngày)
     Đến: 17/12/2025 (Cả ngày)
     Số ngày: 3 ngày
     Lý do: Việc gia đình
     ━━━━━━━━━━━━━━━━━━━━
     [✅ Gửi yêu cầu] [❌ Hủy]

User: [✅ Gửi yêu cầu]

Bot: ✅ Đã gửi yêu cầu nghỉ phép!
     Mã yêu cầu: #NP-2025120801
     Đang chờ phê duyệt từ quản lý.
```

### Flow 3: Manager Approval (Group Chat)
```
Bot posts to group:
━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 YÊU CẦU NGHỈ PHÉP #NP-2025120801
━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Người gửi: Jones (jones@nerdlabs.tech)
👔 Quản lý: @boss
📌 Loại: Nghỉ phép
📅 Từ: 15/12/2025 (Cả ngày)
📅 Đến: 17/12/2025 (Cả ngày)
⏱ Số ngày: 3 ngày
📝 Lý do: Việc gia đình
🕐 Gửi lúc: 08/12/2025 10:30
━━━━━━━━━━━━━━━━━━━━━━━━━━

[✅ Duyệt] [❌ Từ chối]
```

When manager clicks [✅ Duyệt]:
```
Bot updates message:
━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ĐÃ DUYỆT #NP-2025120801
━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Người gửi: Jones
📌 Loại: Nghỉ phép
📅 15/12/2025 - 17/12/2025
✅ Duyệt bởi: @boss (08/12/2025 11:00)
━━━━━━━━━━━━━━━━━━━━━━━━━━

Bot DMs user:
✅ Yêu cầu #NP-2025120801 đã được duyệt!

Bot actions:
- Write to "Raw" sheet
- Remove from pending_requests.json
```

When **wrong manager** clicks button:
```
Bot shows popup alert:
❌ Bạn không có quyền duyệt yêu cầu này.
Chỉ quản lý được chỉ định mới có thể duyệt.
```
(Message remains unchanged, buttons still active for correct manager)

### Flow 4: 24-Hour Reminder (Scheduled Task)
```
Bot checks every hour for pending requests > 24 hours old in pending_requests.json.

If found and reminder not yet sent:
Bot DMs manager:
━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ NHẮC NHỞ DUYỆT YÊU CẦU
━━━━━━━━━━━━━━━━━━━━━━━━━━
Pls check the employee leave request

📋 Yêu cầu: #NP-2025120801
👤 Nhân viên: Jones
📅 Ngày gửi: 07/12/2025 10:30
⏱ Đã chờ: 24 giờ
━━━━━━━━━━━━━━━━━━━━━━━━━━
[Xem trong nhóm]

Bot marks reminder_sent = true in pending_requests.json.
```

---

## Project Structure

```
telegram-leave-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point, bot setup
│   ├── config.py            # Bot token, Sheet ID, Group ID
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py         # /start command (auto-registration check)
│   │   ├── leave.py         # /nghiphep conversation flow
│   │   └── approval.py      # Manager approval callbacks + authorization check
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── calendar.py      # Date picker keyboard
│   │   ├── leave_type.py    # Leave type selection
│   │   └── shift.py         # Shift selection (Sáng/Chiều/Cả ngày)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── google_sheet.py  # Read/write to Google Sheets via Apps Script API
│   │   ├── pending_store.py # Read/write pending_requests.json
│   │   └── reminder.py      # 24-hour reminder scheduler
│   └── utils/
│       ├── __init__.py
│       └── date_utils.py    # Date formatting, weekend check
├── data/
│   └── pending_requests.json # Local storage for pending requests
├── requirements.txt
├── .env                     # BOT_TOKEN, SHEET_API_URL, APPROVAL_GROUP_ID
└── README.md
```

---

## Key Dependencies

```
python-telegram-bot>=20.0    # Telegram bot framework (async)
httpx                        # HTTP client for Google Apps Script API
python-dotenv                # Environment variables
apscheduler                  # Scheduled tasks (24-hour reminder)
```

---

## Google Sheet Integration

### "Nhân sự" Sheet (Admin adds 2 columns)
| Name | Email | ... | Telegram Username | Manager Email |
|------|-------|-----|-------------------|---------------|
| Jones | jones@nerdlabs.tech | ... | @jones | boss@nerdlabs.tech |
| Boss | boss@nerdlabs.tech | ... | @boss | ceo@nerdlabs.tech |

**Bot reads:**
- `Telegram Username` → to identify employee from Telegram @
- `Manager Email` → to find manager's row and get their Telegram @

### "Raw" Sheet (Only approved requests)
Bot writes new rows ONLY after manager approves:
- STT: Auto-increment
- Loại Hình: From user selection
- Người Gửi: Employee email (from Nhân sự lookup)
- Quản Lý: Manager email (from Nhân sự lookup)
- Lý Do: From user input
- Mô tả: "Submitted via Telegram Bot"
- Thời gian bắt đầu: Selected start date
- Ca bắt đầu: Selected shift
- Thời gian kết thúc: Selected end date (if range)
- Ca kết thúc: Selected shift
- Tạo lúc: Request creation time
- Duyệt bởi: Manager email
- Duyệt lúc: Approval timestamp
- Revoked: "No"

**Rejected/ignored requests:** NOT written to Raw sheet

---

## Google Apps Script API Endpoint

Add to `main` file:

```javascript
function doPost(e) {
    const data = JSON.parse(e.postData.contents);
    const action = data.action;

    switch(action) {
        case 'get_employee_by_telegram':
            return getEmployeeByTelegram(data.telegram_username);
        case 'get_employees':
            return getAllEmployees();
        case 'approve_leave':
            return approveLeave(data);
    }
}

function getEmployeeByTelegram(telegramUsername) {
    // Search "Nhân sự" sheet for row with matching Telegram Username
    // Return: { email, name, manager_email, manager_telegram }
}

function getAllEmployees() {
    // Return all employees with their Telegram usernames
    // Used for manager lookup
}

function approveLeave(data) {
    // Write approved request to "Raw" sheet
}
```

Deploy as Web App to get endpoint URL.

---

## Implementation Steps

### Phase 1: Setup (Manual)
1. Create Telegram bot via @BotFather → get BOT_TOKEN
2. Create Telegram group for approvals → get APPROVAL_GROUP_ID
3. Add bot to the approval group as admin
4. Add "Telegram Username" and "Manager Email" columns to "Nhân sự" sheet
5. Deploy Google Apps Script as Web App → get SHEET_API_URL

### Phase 2: Python Project Setup
6. Create project structure
7. Setup config.py with environment variables
8. Implement google_sheet.py service (API calls to Apps Script)
9. Implement pending_store.py (read/write pending_requests.json)
10. Test API connection

### Phase 3: Auto-Registration Flow
11. Implement /start command (auto-check Telegram username in Nhân sự)
12. Test auto-registration lookup

### Phase 4: Leave Request Flow
13. Implement calendar keyboard (date picker)
14. Implement leave type keyboard (WFH/Nghỉ phép/Nghỉ không lương)
15. Implement shift keyboard (Sáng/Chiều/Cả ngày)
16. Implement /nghiphep conversation handler
17. Implement confirmation message and save to pending_requests.json
18. Test leave request flow

### Phase 5: Approval Flow
19. Implement posting to approval group with inline buttons
20. Implement manager lookup (find manager's Telegram from Nhân sự)
21. Implement manager authorization check (only assigned manager can approve)
22. Implement approve callback → write to Raw sheet, remove from JSON
23. Implement reject callback → remove from JSON
24. Implement user notification (DM result)
25. Test approval flow

### Phase 6: Reminder System
26. Implement reminder.py with APScheduler
27. Check pending_requests.json for requests > 24 hours old
28. Send DM reminder to manager
29. Mark reminder_sent = true in JSON
30. Test reminder flow

### Phase 7: Final Testing
31. End-to-end testing
32. Error handling and edge cases
33. Deploy to server

---

## Files to Create/Modify

### Python Bot (New)
| File | Description |
|------|-------------|
| `telegram-leave-bot/bot/main.py` | Entry point, bot application setup |
| `telegram-leave-bot/bot/config.py` | Environment variables loader |
| `telegram-leave-bot/bot/handlers/start.py` | /start command (auto-registration) |
| `telegram-leave-bot/bot/handlers/leave.py` | /nghiphep conversation flow |
| `telegram-leave-bot/bot/handlers/approval.py` | Approval callbacks with auth check |
| `telegram-leave-bot/bot/keyboards/calendar.py` | Date picker inline keyboard |
| `telegram-leave-bot/bot/keyboards/leave_type.py` | Leave type selection |
| `telegram-leave-bot/bot/keyboards/shift.py` | Shift selection |
| `telegram-leave-bot/bot/services/google_sheet.py` | API client for Apps Script |
| `telegram-leave-bot/bot/services/pending_store.py` | Read/write pending_requests.json |
| `telegram-leave-bot/bot/services/reminder.py` | 24-hour reminder scheduler |
| `telegram-leave-bot/bot/utils/date_utils.py` | Date formatting helpers |
| `telegram-leave-bot/data/pending_requests.json` | Local storage for pending requests |
| `telegram-leave-bot/requirements.txt` | Python dependencies |
| `telegram-leave-bot/.env.example` | Environment template |

### Google Apps Script (Modify existing)
| File | Changes |
|------|---------|
| `main` | Add `doPost()` API endpoint for: get_employee_by_telegram, get_employees, approve_leave |

### Google Sheets (Manual)
| Sheet | Action |
|-------|--------|
| "Nhân sự" | Add "Telegram Username" and "Manager Email" columns (admin fills) |

---

## Security & Validation Rules

1. **Auto-registration:** Bot matches user's Telegram @ with "Telegram Username" column in "Nhân sự" sheet
2. **Leave requests:** Only users found in "Nhân sự" can submit
3. **Manager must be in system:**
   - When employee submits request, bot looks up Manager Email
   - Finds manager's row in "Nhân sự" to get their Telegram @
   - If manager has no Telegram @ → Block submission:
     "❌ Quản lý của bạn chưa có Telegram trong hệ thống. Vui lòng liên hệ HR."
4. **Approval authorization:**
   - Get manager email from employee's row in "Nhân sự"
   - Look up manager's Telegram @ from their row in "Nhân sự"
   - Only that Telegram user can click approve/reject
   - Others get error popup: "Bạn không có quyền duyệt yêu cầu này"
5. **Environment secrets:** BOT_TOKEN, SHEET_API_URL stored in .env
6. **Audit trail:** Pending requests stored in local JSON file until approved/rejected

---

## YOUR COMMENTS

<!-- Add your comments, questions, or requested changes below -->




