import os
import socket
import time

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURATION
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

UDP_HOST = "127.0.0.1"
UDP_PORT = 9999

PACKET_DATA = b"UDP_TEST_PACKET"
PACKET_COUNT = 10


# =========================
# UDP TEST
# =========================

def udp_test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sent = 0

    try:
        for _ in range(PACKET_COUNT):
            sock.sendto(PACKET_DATA, (UDP_HOST, UDP_PORT))
            sent += 1
            time.sleep(0.05)

    finally:
        sock.close()

    return sent


# =========================
# TELEGRAM COMMANDS
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "🤖 Bot is online!\n\n"
        "/test - Run localhost UDP test\n"
        "/status - Check bot status"
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "✅ Bot status: ONLINE\n"
        "🎯 UDP destination: 127.0.0.1\n"
        "📦 Test packets: 10"
    )


async def test(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "🧪 Starting localhost UDP test..."
    )

    sent = udp_test()

    await update.message.reply_text(
        f"✅ Test completed.\n"
        f"📦 Packets sent: {sent}\n"
        f"🎯 Destination: 127.0.0.1:{UDP_PORT}"
    )


# =========================
# MESSAGE HANDLER
# =========================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text

    await update.message.reply_text(
        f"You said: {text}"
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("status", status)
    )

    app.add_handler(
        CommandHandler("test", test)
    )

    # Normal messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    print("🤖 Telegram bot started")

    app.run_polling()


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()