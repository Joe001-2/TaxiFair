"""
Reply keyboards used during the survey (e.g. contact sharing).
"""

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from bot.translations import t


def contact_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Keyboard prompting the user to share their contact."""
    # We use a reply keyboard here because inline keyboards
    # cannot request contact info.
    btn = KeyboardButton(text=t("btn_contact", lang), request_contact=True)
    return ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)


def cancel_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Simple keyboard with Cancel and Restart options."""
    return ReplyKeyboardMarkup(
        [[t("btn_cancel", lang), t("btn_restart", lang)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Utility to hide the reply keyboard."""
    return ReplyKeyboardRemove()
