"""
Inline keyboards for destination, morning time, and frequency selection.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DESTINATIONS, MORNING_SLOTS, FREQUENCY_OPTIONS
from bot.translations import t

def _build_grid(items: list[str], lang: str, prefix: str, columns: int = 2) -> InlineKeyboardMarkup:
    """Build an inline keyboard grid from a list of keys, mapping them to translated text."""
    buttons = []
    for item in items:
        # Check for specific translation keys
        if item in DESTINATIONS:
            label = t(f"opt_{item}", lang)
        elif item == "12:00 - 12:15 LT":
            label = t("opt_12_15", lang)
        elif item == "12:15 - 12:30 LT":
            label = t("opt_12_30", lang)
        elif item == "12:45 - 1:00 LT":
            label = t("opt_1_00", lang)
        elif item == "Monday to Friday":
            label = t("opt_mon_fri", lang)
        elif item == "Monday to Saturday":
            label = t("opt_mon_sat", lang)
        else:
            label = t(f"opt_{item}", lang)
            
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"{prefix}:{item}"))

    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(buttons), columns):
        rows.append(buttons[i : i + columns])
    return InlineKeyboardMarkup(rows)


def dynamic_choice_keyboard(options: list[str], lang: str = "en", prefix: str = "opt", columns: int = 2) -> InlineKeyboardMarkup:
    """Generic inline keyboard for any list of options."""
    return _build_grid(options, lang, prefix, columns=columns)


def confirmation_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Inline keyboard for final submission confirmation."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_submit", lang), callback_data="confirm:yes"),
            InlineKeyboardButton(t("btn_cancel", lang), callback_data="confirm:no"),
        ],
        [
            InlineKeyboardButton(t("btn_restart", lang), callback_data="confirm:restart"),
        ],
    ])
