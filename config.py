"""
Configuration module for the Beshale Condominium Transport Registration Bot.

All secrets and configurable values are loaded from environment variables.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present (for local development)
load_dotenv()


# ──────────────────────────────────────────────
# Telegram Bot
# ──────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required.")

ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
if ADMIN_ID == 0:
    logging.warning("ADMIN_ID not set — admin commands will be disabled.")


# ──────────────────────────────────────────────
# Google Sheets
# ──────────────────────────────────────────────
SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "")
SUMMARY_SPREADSHEET_ID: str = os.getenv("SUMMARY_SPREADSHEET_ID", "1bCWLUtZUbnPZzd0LNrm8LOeMAEcBQ0f6upDxvFzFxCA")
if not SPREADSHEET_ID:
    raise RuntimeError("SPREADSHEET_ID environment variable is required.")

# Google credentials: either a JSON string or a file path
GOOGLE_CREDENTIALS_JSON: str = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "")

if not GOOGLE_CREDENTIALS_JSON and not GOOGLE_CREDENTIALS_PATH:
    raise RuntimeError(
        "Provide GOOGLE_CREDENTIALS_JSON (raw JSON string) or "
        "GOOGLE_CREDENTIALS_PATH (path to service-account JSON file)."
    )


def get_google_credentials_info() -> dict:
    """Return parsed Google service-account credentials as a dict."""
    if GOOGLE_CREDENTIALS_JSON:
        return json.loads(GOOGLE_CREDENTIALS_JSON)
    path = Path(GOOGLE_CREDENTIALS_PATH)
    if not path.is_file():
        raise FileNotFoundError(
            f"Google credentials file not found: {GOOGLE_CREDENTIALS_PATH}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


# ──────────────────────────────────────────────
# Sheet tab names
# ──────────────────────────────────────────────
SHEET_REGISTRATIONS: str = os.getenv("SHEET_NAME", "registrations")
SHEET_USERS: str = "users"
SHEET_SETTINGS: str = "settings"
SHEET_LOGS: str = "logs"


# ──────────────────────────────────────────────
# Timezone & logging
# ──────────────────────────────────────────────
TIMEZONE: str = os.getenv("TIMEZONE", "Africa/Addis_Ababa")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


# ──────────────────────────────────────────────
# Survey options (kept here so they're easy to
# change without touching handler code)
# ──────────────────────────────────────────────
DESTINATIONS: list[str] = [
    "Megenagna",
    "Bole",
    "Mexico",
    "Piassa",
    "Torhayloch",
    "Goro",
    "Merkato",
]

MORNING_SLOTS: list[str] = [
    "12:00 - 12:15 LT",
    "12:15 - 12:30 LT",
    "12:45 - 1:00 LT",
]

FREQUENCY_OPTIONS: list[str] = [
    "Monday to Friday",
    "Monday to Saturday",
]

# Duplicate-submission cooldown in seconds (default 5 minutes)
DUPLICATE_COOLDOWN_SECONDS: int = int(os.getenv("DUPLICATE_COOLDOWN_SECONDS", "300"))
