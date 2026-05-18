# 🚍 Beshale Condominium Transport Registration Bot

A production-ready Telegram bot that collects transportation registration data from residents of Beshale Condominium. All submissions are stored in Google Sheets in real time.

---

## Features

- **Step-by-step survey** — 9 questions asked one at a time in Telegram DM
- **Telegram contact sharing** — phone number collected via native contact button
- **Inline keyboards** — destination, morning time, and frequency selection via buttons
- **Input validation** — every field validated; invalid input triggers a clear error and repeats the question
- **Google Sheets storage** — submissions saved immediately with full schema (19 columns)
- **Duplicate protection** — prevents re-submission within a configurable cooldown
- **Admin commands** — `/stats`, `/export` (CSV), `/all`, `/help` restricted by user ID
- **Admin notifications** — real-time Telegram alert on each new submission
- **Auto-setup** — missing sheet tabs and headers are created automatically on first run
- **Structured logging** — logs to console and to a `logs` tab in the spreadsheet

---

## Project Structure

```
TaxiFair/
├── main.py                  # Entry point — starts the bot
├── config.py                # Loads env vars, defines survey options
├── requirements.txt         # Python dependencies
├── .env.example             # Template for environment variables
├── .gitignore
├── bot/
│   ├── handlers/
│   │   ├── start.py         # /start command & welcome message
│   │   ├── survey.py        # All 9 survey question handlers + confirmation
│   │   └── admin.py         # /stats, /export, /all, /help
│   ├── keyboards/
│   │   ├── reply_keyboards.py   # Contact sharing button
│   │   └── inline_keyboards.py  # Destination, time, frequency buttons
│   ├── states/
│   │   └── survey_states.py     # FSM state constants
│   └── utils/
│       └── helpers.py           # ID generation, timestamps, summaries
└── services/
    ├── google_sheets.py     # Google Sheets read/write service
    ├── validators.py        # Input validation for every field
    └── logger.py            # Console + Sheets logging
```

---

## Setup Instructions

### 1. Create the Telegram Bot

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts to name your bot.
3. Copy the **bot token** (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).

### 2. Find Your Admin Telegram ID

1. Search for **@userinfobot** on Telegram.
2. Send `/start` — it will reply with your numeric user ID.
3. Save this number for the `ADMIN_ID` variable.

### 3. Set Up Google Cloud & Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or use an existing one).
3. Navigate to **APIs & Services → Library**.
4. Search for and enable **Google Sheets API**.
5. Search for and enable **Google Drive API**.
6. Go to **APIs & Services → Credentials**.
7. Click **Create Credentials → Service Account**.
8. Give it a name (e.g. `beshale-bot`) and click **Done**.
9. Click on the service account → **Keys → Add Key → Create new key → JSON**.
10. Download the JSON file and save it as `credentials.json` in the project root.

### 4. Create & Share the Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com/) and create a new blank spreadsheet.
2. Name it (e.g. `Beshale Transport Registrations`).
3. Copy the **spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```
4. Click **Share** and add the service account email address (found in the JSON file under `client_email`, e.g. `beshale-bot@project.iam.gserviceaccount.com`).
5. Grant **Editor** access.

> **Note:** The bot will automatically create the required tabs (`registrations`, `users`, `settings`, `logs`) and their header rows on first launch. You do not need to set them up manually.

### 5. Configure Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_ID=987654321
SPREADSHEET_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ
GOOGLE_CREDENTIALS_PATH=credentials.json
```

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Telegram bot token from BotFather |
| `ADMIN_ID` | ✅ | Your Telegram numeric user ID |
| `SPREADSHEET_ID` | ✅ | Google Sheets spreadsheet ID |
| `GOOGLE_CREDENTIALS_PATH` | ✅* | Path to service-account JSON file |
| `GOOGLE_CREDENTIALS_JSON` | ✅* | OR the full JSON as a single-line string |
| `SHEET_NAME` | ❌ | Main tab name (default: `registrations`) |
| `TIMEZONE` | ❌ | Timezone (default: `Africa/Addis_Ababa`) |
| `LOG_LEVEL` | ❌ | Logging level (default: `INFO`) |
| `DUPLICATE_COOLDOWN_SECONDS` | ❌ | Seconds between allowed submissions (default: `300`) |

*Provide either `GOOGLE_CREDENTIALS_PATH` or `GOOGLE_CREDENTIALS_JSON`, not both.

### 6. Install Dependencies

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 7. Run the Bot

```bash
python main.py
```

You should see:
```
Connected to Google Sheets (ID: ...)
Bot is starting... Press Ctrl+C to stop.
```

---

## Testing the Full Flow

1. Open your bot in Telegram (find it by the username you gave BotFather).
2. Send `/start`.
3. Answer all 9 questions:
   - Type your full name
   - Tap "📱 Share Contact" to share your phone number
   - Type your block number
   - Type your house number
   - Type the number of household members
   - Tap a destination button (Megenagna, Bole, Mexico, Piassa, Torhayloch, Goro, Merkato)
   - Tap a morning departure time button
   - Type your evening pickup time
   - Tap a service frequency button
4. Review the summary and tap **✅ Submit**.
5. Open your Google Sheet — the new row should appear in the `registrations` tab.
6. If you set `ADMIN_ID`, you should also receive a notification message.

---

## Admin Commands

| Command | Description |
|---------|-------------|
| `/stats` | Total submission count and breakdown by destination |
| `/export` | Download all registrations as a CSV file |
| `/all` | View the last 10 registrations |
| `/help` | Show available commands |
| `/cancel` | Cancel a registration in progress |

All admin commands (except `/help` and `/cancel`) are restricted to the `ADMIN_ID`.

---

## Google Sheets Schema

### `registrations` tab (19 columns)

| Column | Description |
|--------|-------------|
| `submission_id` | Unique 12-character ID |
| `telegram_user_id` | User's Telegram numeric ID |
| `telegram_username` | Telegram @username |
| `telegram_first_name` | Telegram first name |
| `telegram_last_name` | Telegram last name |
| `full_name` | Self-reported full name |
| `contact_phone` | Phone from contact share |
| `block_number` | Condominium block |
| `house_number` | House number |
| `household_people_count` | People needing transport |
| `destination` | Selected destination |
| `morning_departure_time` | Selected morning slot |
| `evening_pickup_time` | Typed evening time |
| `service_frequency` | Mon–Fri or Mon–Sat |
| `registration_date` | YYYY-MM-DD |
| `registration_time` | HH:MM:SS |
| `submitted_at_iso` | ISO 8601 timestamp |
| `status` | Default: `new` |
| `notes` | Admin notes (blank) |

### Supporting tabs

- **`users`** — tracks Telegram user metadata and submission count
- **`settings`** — key-value store for configurable options
- **`logs`** — timestamped event log for errors and activity

---

## Deployment

### Option A: VPS / Cloud VM

```bash
# On the server
git clone <your-repo-url>
cd TaxiFair
pip install -r requirements.txt
# Set environment variables or copy .env
python main.py
```

For persistence, use `systemd`, `supervisor`, or `tmux`/`screen`:

```bash
# Quick background run
nohup python main.py > bot.log 2>&1 &
```

### Option B: Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
docker build -t beshale-bot .
docker run -d --env-file .env --name beshale-bot beshale-bot
```

### Option C: Railway / Render / Fly.io

1. Push your code to GitHub.
2. Connect the repo to your platform.
3. Set environment variables in the platform dashboard.
4. Use `python main.py` as the start command.

---

## Data Protection

- **No local storage** — all data lives in Google Sheets, protected by Google's infrastructure.
- **Secrets in environment variables** — bot token, credentials, and admin ID are never hardcoded.
- **Service account isolation** — the Google service account only has access to the specific spreadsheet you share with it.
- **Admin-restricted commands** — sensitive operations are gated by Telegram user ID.
- **Duplicate protection** — prevents accidental double submissions within the cooldown window.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `BOT_TOKEN environment variable is required` | Set `BOT_TOKEN` in your `.env` file |
| `SPREADSHEET_ID environment variable is required` | Set `SPREADSHEET_ID` in your `.env` file |
| `Google credentials file not found` | Check `GOOGLE_CREDENTIALS_PATH` points to the correct JSON file |
| Bot doesn't respond | Make sure `python main.py` is running and the token is correct |
| Sheets not updating | Verify the spreadsheet is shared with the service account email as Editor |
| `APIError: quota exceeded` | Google Sheets API has rate limits; the bot handles this gracefully |
| Admin commands don't work | Verify `ADMIN_ID` matches your Telegram numeric user ID |

---

## License

MIT
