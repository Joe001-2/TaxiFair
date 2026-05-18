"""
/start command handler — entry point for the survey conversation.
"""

import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Fix for ModuleNotFoundError when running this file directly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from bot.states.survey_states import ASKING_QUESTIONS, CHOOSING_LANGUAGE
from bot.keyboards.reply_keyboards import remove_keyboard
from bot.translations import t


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start — send language selection."""
    import os
    
    # Clear any leftover data from a previous run
    context.user_data.clear()
    context.user_data["current_question_index"] = 0

    logo_path = "logo.png"
    text = t("choose_lang", "en")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("English", callback_data="lang:en"), InlineKeyboardButton("አማርኛ", callback_data="lang:am")],
        [InlineKeyboardButton("Afaan Oromoo", callback_data="lang:or"), InlineKeyboardButton("ትግርኛ", callback_data="lang:ti")]
    ])

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    
    return CHOOSING_LANGUAGE

async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's language selection."""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    _, lang = query.data.split(":")
    context.user_data["language"] = lang
    
    welcome_text = t("welcome", lang)
    await query.message.reply_text(welcome_text, parse_mode="HTML")
    
    from bot.handlers.survey import ask_question
    return await ask_question(update, context)
