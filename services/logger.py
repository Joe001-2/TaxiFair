"""
Structured logger that also writes to the Google Sheets 'logs' tab.
"""

import logging
from datetime import datetime

import pytz

from config import TIMEZONE, LOG_LEVEL

# ── Standard Python logger ───────────────────────────────────
logger = logging.getLogger("beshale_bot")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_console = logging.StreamHandler()
_console.setFormatter(_formatter)
logger.addHandler(_console)


def _now_str() -> str:
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).isoformat()


def log_event(level: str, event: str, details: str = "") -> None:
    """
    Log to both the Python logger and (lazily) to the Sheets 'logs' tab.
    We import sheets_service here to avoid circular imports.
    """
    getattr(logger, level.lower(), logger.info)(f"{event} — {details}")
    try:
        from services.google_sheets import sheets_service
        import asyncio
        # Since log_event is often called from sync contexts or fire-and-forget,
        # we try to schedule the task if an event loop is running.
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(sheets_service.append_log(
                    timestamp=_now_str(),
                    level=level.upper(),
                    event=event,
                    details=details,
                ))
        except RuntimeError:
            # No running loop, we can't easily log to sheets from here sync-only
            pass
    except Exception:
        # If sheets logging fails, don't crash the bot
        logger.debug("Could not write log to Google Sheets.", exc_info=True)
