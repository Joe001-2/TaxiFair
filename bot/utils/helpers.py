"""
Utility helpers: ID generation, timestamp formatting, summary building.
"""

import uuid
from datetime import datetime

import pytz

from config import TIMEZONE


def generate_submission_id() -> str:
    """Return a short, unique submission ID."""
    return uuid.uuid4().hex[:12].upper()


def now_tz() -> datetime:
    """Return the current datetime in the configured timezone."""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)


def format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M:%S")


def format_iso(dt: datetime) -> str:
    return dt.isoformat()


def build_summary(data: dict, lang: str = "en") -> str:
    """Build a human-readable summary of the registration data."""
    from bot.survey_config import TRANSPORT_SURVEY
    from bot.translations import t
    import html
    
    lines = [
        t("summary_title", lang),
        "",
    ]
    
    for question in TRANSPORT_SURVEY.questions:
        label = t(question.label, lang)
        val = data.get(question.id, "—")
        if isinstance(question.options, list) and val in question.options:
            val = t(f"opt_{val}", lang)
        value = html.escape(str(val))
        lines.append(f"🔹 <b>{label}:</b> {value}")
        
    return "\n".join(lines)
