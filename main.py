import logging
import asyncio
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from bot.states.survey_states import (
    ASKING_QUESTIONS, CONFIRMATION, CHOOSING_LANGUAGE
)
from bot.handlers.start import start_command, handle_language_choice
from bot.handlers.survey import (
    handle_answer, handle_confirmation, cancel_command,
)
from bot.handlers.admin import (
    stats_command, export_command, all_command, help_command,
)
from services.google_sheets import sheets_service
from services.logger import logger

import asyncio
import sys

# Windows-specific fix for "RuntimeError: There is no current event loop"
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def connect_sheets() -> None:
    """Connect to Google Sheets."""
    logger.info("Connecting to Google Sheets...")
    try:
        sheets_service.connect()
        logger.info("Google Sheets connected successfully.")
    except Exception as e:
        logger.error("Failed to connect to Google Sheets: %s", e)
        raise e


def create_application() -> Application:
    """Create and configure the python-telegram-bot application."""
    # ── Build the application ────────────────────────────────
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # ── Survey conversation handler ──────────────────────────
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            CHOOSING_LANGUAGE: [
                CallbackQueryHandler(handle_language_choice, pattern=r"^lang:"),
            ],
            ASKING_QUESTIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer),
                MessageHandler(filters.CONTACT, handle_answer),
                CallbackQueryHandler(handle_answer, pattern=r"^q\d+:"),
            ],
            CONFIRMATION: [
                CallbackQueryHandler(handle_confirmation, pattern=r"^confirm:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
        ],
        allow_reentry=True,
    )
    app.add_handler(conv_handler)

    # ── Admin / utility commands (outside conversation) ──────
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("all", all_command))
    app.add_handler(CommandHandler("help", help_command))

    return app


async def run_bot() -> None:
    """Run the bot in polling mode (local development)."""
    # ── Connect to Google Sheets ─────────────────────────────
    connect_sheets()

    # ── Build and configure application ──────────────────────
    app = create_application()

    # ── Start polling ────────────────────────────────────────
    logger.info("Bot is starting... Press Ctrl+C to stop.")
    
    # We use a context manager to ensure the bot starts and stops gracefully
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        # Keep the bot running until interrupted
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
    except Exception as exc:
        logger.error("Bot crashed: %s", exc, exc_info=True)
