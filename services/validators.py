"""
Input validators for survey answers.
"""

from config import DESTINATIONS, MORNING_SLOTS, FREQUENCY_OPTIONS
from bot.translations import t


def validate_full_name(text: str, lang: str = "en") -> tuple[bool, str]:
    """Name must be non-empty and at least 2 characters."""
    text = text.strip()
    if not text or len(text) < 2:
        return False, t('val_name', lang)
    return True, text


def validate_block_number(text: str, lang: str = "en") -> tuple[bool, str]:
    """Block number must be non-empty."""
    text = text.strip()
    if not text:
        return False, t('val_block', lang)
    return True, text


def validate_house_number(text: str, lang: str = "en") -> tuple[bool, str]:
    """House number must be non-empty."""
    text = text.strip()
    if not text:
        return False, t('val_house', lang)
    return True, text


def validate_phone_number(text: str, lang: str = "en") -> tuple[bool, str]:
    """Phone number must contain at least 7 digits."""
    text = text.strip()
    # Extract digits only
    digits = ''.join(filter(str.isdigit, text))
    if len(digits) < 7:
        return False, t('val_phone', lang)
    return True, text


def validate_household_count(text: str, lang: str = "en") -> tuple[bool, str]:
    """Must be a positive integer."""
    text = text.strip()
    try:
        count = int(text)
        if count <= 0:
            raise ValueError
    except ValueError:
        return False, t('val_count', lang)
    return True, str(count)


def validate_destination(value: str, lang: str = "en") -> tuple[bool, str]:
    """Must be one of the approved destinations."""
    if value not in DESTINATIONS:
        return False, t('val_dest', lang)
    return True, value


def validate_morning_time(value: str, lang: str = "en") -> tuple[bool, str]:
    """Must be one of the approved morning slots."""
    if value not in MORNING_SLOTS:
        return False, t('val_morning', lang)
    return True, value


def validate_evening_time(text: str, lang: str = "en") -> tuple[bool, str]:
    """Evening pickup time — free text but cannot be empty."""
    text = text.strip()
    if not text:
        return False, t('val_evening', lang)
    return True, text


def validate_frequency(value: str, lang: str = "en") -> tuple[bool, str]:
    """Must be one of the approved frequency options."""
    if value not in FREQUENCY_OPTIONS:
        return False, t('val_freq', lang)
    return True, value
