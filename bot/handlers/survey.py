"""
Generic survey conversation handler.
"""

import sys
import os
import html
from datetime import datetime

# Fix for ModuleNotFoundError when running this file directly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.states.survey_states import ASKING_QUESTIONS, CONFIRMATION
from bot.keyboards.reply_keyboards import contact_keyboard, remove_keyboard
from bot.keyboards.inline_keyboards import (
    dynamic_choice_keyboard, confirmation_keyboard,
)
from bot.utils.helpers import (
    generate_submission_id, now_tz, format_date,
    format_time, format_iso, build_summary,
)
from services.google_sheets import sheets_service
from services.logger import log_event, logger
from config import ADMIN_ID, DUPLICATE_COOLDOWN_SECONDS
from bot.survey_config import TRANSPORT_SURVEY
from bot.translations import t

def _esc(text: str) -> str:
    """Escape text for HTML parse mode."""
    return html.escape(str(text))

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the current question based on current_question_index."""
    idx = context.user_data.get("current_question_index", 0)
    lang = context.user_data.get("language", "en")
    survey = TRANSPORT_SURVEY
    # Calculate dynamic question numbering
    q_num = idx + 1
    q_total = len(survey.questions)
            
    if idx >= len(survey.questions):
        # All questions answered, show summary and confirmation
        summary = build_summary(context.user_data, lang)
        text = (
            f"{summary}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{t('review_prompt', lang)}"
        )
        if update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode="HTML", reply_markup=confirmation_keyboard())
        else:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=confirmation_keyboard())
        return CONFIRMATION

    question = survey.questions[idx]
    keyboard = remove_keyboard()
    
    prefix = t('q_prefix', lang, num=q_num, total=q_total)
    q_text = f"{prefix}{t(question.text, lang)}"
    
    if question.type == "contact":
        keyboard = contact_keyboard(lang)
    elif question.type == "choice" and question.options:
        keyboard = dynamic_choice_keyboard(question.options, lang, prefix=f"q{idx}")

    if update.callback_query:
        await update.callback_query.message.reply_text(q_text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(q_text, parse_mode="HTML", reply_markup=keyboard)
    
    return ASKING_QUESTIONS

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's answer to the current question."""
    idx = context.user_data.get("current_question_index", 0)
    survey = TRANSPORT_SURVEY
    question = survey.questions[idx]
    
    lang = context.user_data.get("language", "en")
    
    answer = None
    if question.type == "contact":
        if not update.message.contact:
            await update.message.reply_text(
                t('err_contact', lang),
                parse_mode="HTML", reply_markup=contact_keyboard(lang),
            )
            return ASKING_QUESTIONS
        answer = update.message.contact.phone_number
    elif question.type == "choice":
        if not update.callback_query:
            await update.message.reply_text(t('err_buttons', lang))
            return ASKING_QUESTIONS
        query = update.callback_query
        try:
            await query.answer()
        except Exception:
            # If the query is too old, just ignore and continue
            pass
        _, answer = query.data.split(":", 1)
    else:
        answer = update.message.text or ""

    # Validation
    if question.validator:
        ok, result = question.validator(answer, lang)
        if not ok:
            # result might contain HTML, so use parse_mode="HTML"
            if update.callback_query:
                await update.callback_query.message.reply_text(result, parse_mode="HTML")
            else:
                await update.message.reply_text(result, parse_mode="HTML")
            return ASKING_QUESTIONS
        answer = result

    # Save answer
    context.user_data[question.id] = answer
    context.user_data["current_question_index"] = idx + 1
    
    return await ask_question(update, context)

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    _, action = query.data.split(":", 1)
    
    lang = context.user_data.get("language", "en")
    
    if action == "no":
        await query.message.reply_text(
            t('msg_cancelled', lang),
            parse_mode="HTML",
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    if action == "restart":
        context.user_data.clear()
        await query.message.reply_text(t('msg_restarting', lang), parse_mode="HTML")
        return ConversationHandler.END
    
    return await _submit(update, context)

async def _submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = query.from_user
    dt = now_tz()
    
    lang = context.user_data.get("language", "en")
    
    # Duplicate check
    try:
        last_iso = await sheets_service.get_user_last_submission_time(user.id)
        if last_iso:
            last_dt = datetime.fromisoformat(last_iso)
            if (dt - last_dt).total_seconds() < DUPLICATE_COOLDOWN_SECONDS:
                await query.message.reply_text(
                    t('err_duplicate', lang),
                    parse_mode="HTML",
                )
                log_event("WARNING", "duplicate_blocked", f"user={user.id}")
                return ConversationHandler.END
    except Exception as exc:
        logger.warning("Duplicate check failed: %s", exc)

    data = context.user_data
    sub_id = generate_submission_id()

    # Build the row with ONLY the requested fields
    row = {
        "full_name": data.get("full_name", ""),
        "telegram_user_id": str(user.id),
        "contact_phone": data.get("contact_phone", ""),
        "block_number": data.get("block_number", ""),
        "destination": data.get("destination", ""),
        "morning_departure_time": data.get("morning_departure_time", ""),
        "evening_pickup_time": data.get("evening_pickup_time", ""),
        "service_frequency": data.get("service_frequency", ""),
        "telegram_username": user.username or "",
    }

    try:
        await sheets_service.append_registration(row)
        await sheets_service.upsert_user(user.id, user.username or "", format_iso(dt))
    except Exception as exc:
        logger.error("Sheets write failed: %s", exc, exc_info=True)
        log_event("ERROR", "sheets_write_failed", str(exc))
        await query.message.reply_text(
            t('err_save', lang),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    await query.message.reply_text(
        t('msg_success', lang, sub_id=_esc(sub_id)),
        parse_mode="HTML",
    )
    log_event("INFO", "registration_submitted", f"id={sub_id} user={user.id}")
    
    if ADMIN_ID:
        try:
            summary = build_summary(data, "en") # Admin always receives English summary
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 <b>New Registration</b>\n\n{summary}\n\nID: <code>{_esc(sub_id)}</code>",
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning("Could not notify admin: %s", exc)
            
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("language", "en")
    context.user_data.clear()
    await update.message.reply_text(
        t('msg_cancelled_start', lang),
        parse_mode="HTML", reply_markup=remove_keyboard(),
    )
    return ConversationHandler.END
