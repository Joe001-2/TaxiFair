"""
Google Sheets service — handles all reads / writes to the spreadsheet.

Uses gspread with a service-account credential.  The spreadsheet must
already exist and be shared with the service-account email address.

On first run the service auto-creates missing tabs and writes header rows.
"""

from __future__ import annotations

import threading
import asyncio
from datetime import datetime
from typing import Any, List, Dict, Optional

import gspread
from google.oauth2.service_account import Credentials

from config import (
    SPREADSHEET_ID,
    SUMMARY_SPREADSHEET_ID,
    SHEET_REGISTRATIONS,
    SHEET_USERS,
    SHEET_SETTINGS,
    SHEET_LOGS,
    get_google_credentials_info,
)
from services.logger import logger
from bot.survey_config import TRANSPORT_SURVEY

# Google API scopes required by gspread
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Mapping of code keys to human-readable sheet headers
REGISTRATION_FIELD_MAP = {
    "full_name": "Full Name",
    "telegram_user_id": "Telegram User ID",
    "contact_phone": "Phone Number",
    "block_number": "Block Number",
    "destination": "Destination",
    "morning_departure_time": "Morning Time",
    "evening_pickup_time": "Evening Time",
    "service_frequency": "Service Frequency",
    "telegram_username": "Username",
}

# The actual headers written to the sheet
REGISTRATION_HEADERS = list(REGISTRATION_FIELD_MAP.values())
# The keys used in the code
REGISTRATION_KEYS = list(REGISTRATION_FIELD_MAP.keys())

# Headers for the summarized sheet
SUMMARY_HEADERS = [
    "Registration Number",
    "Full Name",
    "Phone Number",
    "Destination",
    "Morning Departure",
    "Evening Return",
    "Registration Date & Time",
]

USERS_HEADERS = [
    "telegram_user_id",
    "telegram_username",
    "first_seen_at",
    "last_seen_at",
    "total_submissions",
]

SETTINGS_HEADERS = ["key", "value", "description"]
LOGS_HEADERS = ["timestamp", "level", "event", "details"]


class GoogleSheetsService:
    """Thread-safe, async-friendly wrapper around Google Sheets."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._gc: gspread.Client | None = None
        self._spreadsheet: gspread.Spreadsheet | None = None
        self._summary_spreadsheet: gspread.Spreadsheet | None = None
        
        # Simple memory cache to speed up repeated lookups
        self._last_submission_cache: Dict[int, str] = {}
        self._user_exists_cache: set[int] = set()
        self._ws_cache: Dict[str, gspread.Worksheet] = {}

    # ── Connection ───────────────────────────────────────────

    def connect(self) -> None:
        """Authenticate and open the spreadsheets (Sync, called on startup)."""
        creds_info = get_google_credentials_info()
        credentials = Credentials.from_service_account_info(creds_info, scopes=_SCOPES)
        self._gc = gspread.authorize(credentials)
        self._spreadsheet = self._gc.open_by_key(SPREADSHEET_ID)
        self._summary_spreadsheet = self._gc.open_by_key(SUMMARY_SPREADSHEET_ID)
        logger.info("Connected to Google Sheets (ID: %s)", SPREADSHEET_ID)
        logger.info("Connected to Summary Sheet (ID: %s)", SUMMARY_SPREADSHEET_ID)
        self._ensure_tabs()

    def _ensure_tabs(self) -> None:
        """Create any missing tabs (Sync)."""
        existing = {ws.title for ws in self._spreadsheet.worksheets()}
        tab_map: dict[str, list[str]] = {
            SHEET_REGISTRATIONS: REGISTRATION_HEADERS,
            SHEET_USERS: USERS_HEADERS,
            SHEET_SETTINGS: SETTINGS_HEADERS,
            SHEET_LOGS: LOGS_HEADERS,
        }

        for tab_name, headers in tab_map.items():
            if tab_name not in existing:
                ws = self._spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
                ws.append_row(headers, value_input_option="RAW")
                logger.info("Created tab '%s' with headers.", tab_name)
            else:
                ws = self._spreadsheet.worksheet(tab_name)
                if not ws.row_values(1):
                    ws.append_row(headers, value_input_option="RAW")

        summary_existing = {ws.title for ws in self._summary_spreadsheet.worksheets()}
        if "Summarized" not in summary_existing:
            ws = self._summary_spreadsheet.add_worksheet(title="Summarized", rows=1000, cols=len(SUMMARY_HEADERS))
            ws.append_row(SUMMARY_HEADERS, value_input_option="RAW")
            logger.info("Created tab 'Summarized' in Summary Sheet.")

    def _ws(self, tab: str) -> gspread.Worksheet:
        if tab not in self._ws_cache:
            self._ws_cache[tab] = self._spreadsheet.worksheet(tab)
        return self._ws_cache[tab]

    # ── Async Helpers ───────────────────────────────────────

    async def _run_async(self, func, *args, **kwargs):
        """Run a synchronous gspread function in a separate thread."""
        return await asyncio.to_thread(func, *args, **kwargs)

    # ── Registrations ────────────────────────────────────────

    async def append_registration(self, row: dict[str, Any], lang: str = "en") -> None:
        """Append a completed registration (Async)."""
        await self._run_async(self._sync_append_registration, row, lang)

    def _sync_append_registration(self, row: dict[str, Any], lang: str) -> None:
        """Internal synchronous append."""
        from bot.survey_config import TRANSPORT_SURVEY
        # Use REGISTRATION_KEYS to pull data in the correct order for the labeled columns
        ordered = [str(row.get(key, "")) for key in REGISTRATION_KEYS]
        
        summary_data = {
            "submission_id": "N/A", # submission_id is no longer in main sheet, but kept for summary
            "full_name": str(row.get("full_name", "")),
            "contact_phone": str(row.get("contact_phone", "")),
            "destination": str(row.get("destination", "")),
            "morning_departure_time": str(row.get("morning_departure_time", "")),
            "evening_pickup_time": str(row.get("evening_pickup_time", "")),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        
        summary_ordered = [
            summary_data["submission_id"],
            summary_data["full_name"],
            summary_data["contact_phone"],
            summary_data["destination"],
            summary_data["morning_departure_time"],
            summary_data["evening_pickup_time"],
            summary_data["timestamp"],
        ]
        
        with self._lock:
            self._ws(SHEET_REGISTRATIONS).append_row(ordered, value_input_option="USER_ENTERED")
            self._summary_spreadsheet.worksheet("Summarized").append_row(summary_ordered, value_input_option="USER_ENTERED")
            
            # Update cache
            user_id = row.get("telegram_user_id")
            if user_id:
                self._last_submission_cache[int(user_id)] = row.get("submitted_at_iso", "")

    async def get_all_registrations(self) -> List[Dict[str, str]]:
        return await self._run_async(self._sync_get_all_registrations)

    def _sync_get_all_registrations(self) -> List[Dict[str, str]]:
        with self._lock:
            records = self._ws(SHEET_REGISTRATIONS).get_all_records()
            # Map labels back to machine keys so the rest of the code (admin, reports) still works
            inverse_map = {v: k for k, v in REGISTRATION_FIELD_MAP.items()}
            mapped_records = []
            for rec in records:
                mapped_records.append({inverse_map.get(k, k): v for k, v in rec.items()})
            return mapped_records

    async def get_user_last_submission_time(self, telegram_user_id: int) -> Optional[str]:
        """Fetch last submission time with local cache optimization (Async)."""
        if telegram_user_id in self._last_submission_cache:
            return self._last_submission_cache[telegram_user_id]
            
        return await self._run_async(self._sync_get_user_last_submission_time, telegram_user_id)

    def _sync_get_user_last_submission_time(self, telegram_user_id: int) -> Optional[str]:
        with self._lock:
            ws = self._ws(SHEET_USERS)
            try:
                cell = ws.find(str(telegram_user_id), in_column=1)
                if cell:
                    # last_seen_at is the 4th column in USERS_HEADERS
                    val = ws.cell(cell.row, 4).value
                    if val:
                        self._last_submission_cache[telegram_user_id] = val
                    return val
                return None
            except Exception:
                return None

    # ── Users tab ────────────────────────────────────────────

    async def upsert_user(self, telegram_user_id: int, username: str, now_iso: str) -> None:
        await self._run_async(self._sync_upsert_user, telegram_user_id, username, now_iso)

    def _sync_upsert_user(self, telegram_user_id: int, username: str, now_iso: str) -> None:
        with self._lock:
            ws = self._ws(SHEET_USERS)
            # Optimization: Use gspread's find to avoid downloading the whole table
            try:
                cell = ws.find(str(telegram_user_id), in_column=1)
                if cell:
                    row_idx = cell.row
                    # Update last_seen_at and total_submissions
                    # Fetch current total first (we could also use col_values here if we wanted to be even faster)
                    current_total = ws.cell(row_idx, 5).value
                    new_total = int(current_total or 0) + 1
                    
                    # Batch update for speed
                    ws.update(f"D{row_idx}:E{row_idx}", [[now_iso, new_total]])
                    return
            except gspread.exceptions.CellNotFound:
                pass
            
            # New user
            ws.append_row([str(telegram_user_id), username, now_iso, now_iso, "1"], value_input_option="RAW")
            self._user_exists_cache.add(telegram_user_id)

    # ── Logs tab ─────────────────────────────────────────────

    async def append_log(self, timestamp: str, level: str, event: str, details: str = "") -> None:
        await self._run_async(self._sync_append_log, timestamp, level, event, details)

    def _sync_append_log(self, timestamp: str, level: str, event: str, details: str) -> None:
        with self._lock:
            self._ws(SHEET_LOGS).append_row([timestamp, level, event, details], value_input_option="RAW")

    # ── Settings tab ─────────────────────────────────────────

    async def get_setting(self, key: str) -> Optional[str]:
        return await self._run_async(self._sync_get_setting, key)

    def _sync_get_setting(self, key: str) -> Optional[str]:
        with self._lock:
            records = self._ws(SHEET_SETTINGS).get_all_records()
        for rec in records:
            if rec.get("key") == key:
                return str(rec.get("value", ""))
        return None


# ── Module-level singleton ───────────────────────────────────
sheets_service = GoogleSheetsService()
