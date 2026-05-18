"""
Admin-only command handlers: /stats, /export, /all, /help.
Restricted to the ADMIN_ID configured in environment variables.
"""

import sys
import os
import html
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

# Fix for ModuleNotFoundError when running this file directly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import ADMIN_ID
from services.google_sheets import sheets_service
from services.logger import logger
from bot.survey_config import TRANSPORT_SURVEY
from bot.translations import t
from bot.utils.reports import generate_excel_report, generate_visual_summary


def _is_admin(user_id: int) -> bool:
    return ADMIN_ID and user_id == ADMIN_ID


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/stats — show registration count and breakdown for all choice questions."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ This command is restricted to administrators.")
        return
    try:
        records = await sheets_service.get_all_registrations()
        total = len(records)
        
        sections = [
            f"📊 <b>Survey Statistics</b>",
            f"Total submissions: <code>{total}</code>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        # Calculate breakdown for each choice question
        for q in TRANSPORT_SURVEY.questions:
            if q.type == "choice":
                counts: dict[str, int] = {}
                
                # Pre-calculate inverse mapping if needed
                inverse_options = {}
                if isinstance(q.options, list):
                    from bot.translations import TRANSLATIONS
                    am_options = TRANSLATIONS.get("am", {})
                    for opt in q.options:
                        am_val = am_options.get(f"opt_{opt}")
                        if am_val:
                            inverse_options[am_val] = opt
                
                for r in records:
                    val = r.get(q.id, "Unknown")
                    # Normalize old Amharic to English
                    if val in inverse_options:
                        val = inverse_options[val]
                        
                    counts[val] = counts.get(val, 0) + 1
                
                # Sort by count descending
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                breakdown = "\n".join(f"  • {html.escape(opt)}: <code>{cnt}</code>" for opt, cnt in sorted_counts)
                sections.append(f"🔹 <b>{t(q.label, 'en')} Breakdown:</b>\n{breakdown or '  (no data)'}")

        await update.message.reply_text("\n\n".join(sections), parse_mode="HTML")
    except Exception as exc:
        logger.error("Stats command failed: %s", exc)
        await update.message.reply_text("⚠️ Could not fetch statistics.")


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/export — send an Excel file and visual charts to the administrator."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ This command is restricted to administrators.")
        return
        
    status_msg = await update.message.reply_text("🔄 Generating reports, please wait...")
    
    try:
        records = await sheets_service.get_all_registrations()
        if not records:
            await status_msg.edit_text("No registrations to export.")
            return

        # 1. Generate Excel
        excel_buf = generate_excel_report(records)
        excel_buf.name = "registrations_report.xlsx"

        # 2. Generate Visuals
        charts = generate_visual_summary(records, TRANSPORT_SURVEY.questions)

        # 3. Send Excel
        await update.message.reply_document(
            document=excel_buf, 
            filename="registrations_report.xlsx",
            caption="📊 <b>Full Registration Report (Excel)</b>",
            parse_mode="HTML"
        )

        # 4. Send Charts
        if charts:
            media = [InputMediaPhoto(c) for c in charts]
            # Telegram allows max 10 media in a group
            for i in range(0, len(media), 10):
                await update.message.reply_media_group(media=media[i:i+10])
        
        await status_msg.delete()
        
    except Exception as exc:
        logger.error("Export command failed: %s", exc, exc_info=True)
        await status_msg.edit_text("⚠️ Could not generate reports.")


async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/all — show the last 10 registrations with key fields."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ This command is restricted to administrators.")
        return
    try:
        records = await sheets_service.get_all_registrations()
        if not records:
            await update.message.reply_text("No registrations yet.")
            return
        
        last_10 = records[-10:]
        lines = []
        
        # Use first two questions as identifying fields in the list
        id_fields = [q.id for q in TRANSPORT_SURVEY.questions[:2]]
        
        for r in last_10:
            ident = " | ".join(html.escape(str(r.get(f, "?"))) for f in id_fields)
            date = r.get("registration_date", "?")
            lines.append(f"• {ident} | <i>{date}</i>")
            
        text = f"📋 <b>Last {len(last_10)} Registrations</b>\n\n" + "\n".join(lines)
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as exc:
        logger.error("All command failed: %s", exc)
        await update.message.reply_text("⚠️ Could not fetch registrations.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — show available commands."""
    if _is_admin(update.effective_user.id):
        text = (
            "🛠 <b>Admin Commands</b>\n\n"
            "/start — Begin a new registration\n"
            "/stats — View registration statistics\n"
            "/export — Download Excel report & charts\n"
            "/all — View last 10 registrations\n"
            "/cancel — Cancel current registration\n"
            "/help — Show this help message"
        )
    else:
        text = (
            "ℹ️ <b>Available Commands</b>\n\n"
            "/start — Begin transport registration\n"
            "/cancel — Cancel current registration\n"
            "/help — Show this help message"
        )
    await update.message.reply_text(text, parse_mode="HTML")
