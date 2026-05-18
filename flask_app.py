"""
Flask application wrapper for the TaxiFair Telegram Bot.
This file serves as the webhook receiver when deploying on PythonAnywhere.
"""

import asyncio
from flask import Flask, request, jsonify
from telegram import Update

from main import create_application, connect_sheets
from config import BOT_TOKEN
from services.logger import logger

# ── Initialize Bot & Sheets ──────────────────────────────────
connect_sheets()
ptb_app = create_application()

# Global state to prevent double initialization of the PTB app
is_initialized = False

# ── Initialize Flask ─────────────────────────────────────────
app = Flask(__name__)


@app.before_request
async def initialize_ptb():
    """Ensure the Telegram bot application is initialized and started."""
    global is_initialized
    if not is_initialized:
        logger.info("Initializing python-telegram-bot application inside Flask...")
        await ptb_app.initialize()
        await ptb_app.start()
        is_initialized = True
        logger.info("Telegram bot initialized and started successfully.")


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def telegram_webhook():
    """Receive and process incoming updates from Telegram via Webhook."""
    try:
        payload = request.get_json(force=True)
        logger.info("Received update payload from Telegram.")
        
        # Convert raw JSON payload to a python-telegram-bot Update object
        update = Update.de_json(payload, ptb_app.bot)
        
        # Process the update using the bot's handler system
        await ptb_app.process_update(update)
        
        return "OK", 200
    except Exception as e:
        logger.error("Error processing update webhook: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def health_check():
    """Health check route to verify the web app is running."""
    return f"TaxiFair Telegram Bot is online and listening! (Initialized: {is_initialized})", 200


if __name__ == "__main__":
    # Local debugging
    app.run(port=8000)
