"""
Render.com entry point for the TaxiFair Telegram Bot.

Runs a Tornado web server with two routes:
  GET  /             → Health check (for UptimeRobot keep-alive pings)
  POST /<BOT_TOKEN>  → Telegram webhook (receives updates)

No Flask or FastAPI needed — Tornado is already installed via
python-telegram-bot[webhooks].
"""

import os
import sys
import json
import asyncio

import tornado.web
import tornado.httpserver
from telegram import Update

from main import create_application, connect_sheets
from config import BOT_TOKEN
from services.logger import logger


# ── Tornado Request Handlers ────────────────────────────────


class HealthCheckHandler(tornado.web.RequestHandler):
    """GET / — Returns 200 so UptimeRobot sees the service as alive."""

    def get(self):
        self.set_status(200)
        self.write("TaxiFair Bot is running ✅")


class TelegramWebhookHandler(tornado.web.RequestHandler):
    """POST /<BOT_TOKEN> — Receives updates from Telegram."""

    async def post(self):
        try:
            payload = json.loads(self.request.body)
            update = Update.de_json(payload, self.application.telegram_app.bot)
            await self.application.telegram_app.process_update(update)
            self.set_status(200)
            self.write({"ok": True})
        except Exception as e:
            logger.error("Webhook processing error: %s", e, exc_info=True)
            self.set_status(500)
            self.write({"ok": False, "error": str(e)})


# ── Main entry point ────────────────────────────────────────


async def main() -> None:
    """Start the webhook server for Render deployment."""

    # ── Connect to Google Sheets ─────────────────────────────
    connect_sheets()

    # ── Build and initialize the Telegram bot ────────────────
    telegram_app = create_application()
    await telegram_app.initialize()
    await telegram_app.start()

    # ── Read Render environment ──────────────────────────────
    PORT = int(os.environ.get("PORT", 10000))
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

    if not RENDER_URL:
        logger.error("RENDER_EXTERNAL_URL is not set — cannot register webhook.")
        sys.exit(1)

    # ── Register webhook with Telegram ───────────────────────
    WEBHOOK_URL = f"{RENDER_URL}/{BOT_TOKEN}"
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    logger.info("Webhook registered: %s", WEBHOOK_URL)

    # ── Create Tornado web application ───────────────────────
    web_app = tornado.web.Application([
        (r"/", HealthCheckHandler),                  # UptimeRobot pings this
        (f"/{BOT_TOKEN}", TelegramWebhookHandler),   # Telegram posts here
    ])
    web_app.telegram_app = telegram_app  # attach so handlers can access it

    # ── Start listening ──────────────────────────────────────
    server = tornado.httpserver.HTTPServer(web_app)
    server.listen(PORT, address="0.0.0.0")
    logger.info("Server listening on 0.0.0.0:%d", PORT)
    logger.info("Health check: GET /")
    logger.info("Bot is online. Press Ctrl+C to stop.")

    # ── Keep running forever ─────────────────────────────────
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
    except Exception as exc:
        logger.error("Bot crashed: %s", exc, exc_info=True)
