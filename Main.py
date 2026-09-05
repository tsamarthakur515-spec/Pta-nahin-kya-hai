import os
import socket
import asyncio
import threading
import time
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

HOST = "127.0.0.1"
PORT = 9999

MAX_PACKETS = 20
DEFAULT_PACKETS = 10
DELAY = 0.10

received_packets = 0
receiver_running = False
lock = threading.Lock()


# ============================================================
# UDP RECEIVER
# ============================================================

def udp_receiver():
    global received_packets, receiver_running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.settimeout(0.5)

    receiver_running = True

    try:
        while receiver_running:
            try:
                data, address = sock.recvfrom(2048)

                with lock:
                    received_packets += 1

                print(
                    f"[UDP] Received {len(data)} bytes "
                    f"from {address}"
                )

            except socket.timeout:
                continue

    except OSError as e:
        print(f"[UDP] Receiver error: {e}")

    finally:
        receiver_running = False
        sock.close()


# ============================================================
# UDP TEST
# ============================================================

def udp_test(packet_count):
    sent = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        for number in range(1, packet_count + 1):

            payload = (
                f"UDP_TEST_PACKET_{number}_"
                f"{time.time_ns()}"
            ).encode()

            sock.sendto(payload, (HOST, PORT))

            sent += 1

            time.sleep(DELAY)

    finally:
        sock.close()

    return sent


# ============================================================
# TELEGRAM COMMANDS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot is online.\n\n"
        "/test [count] - Run UDP test\n"
        "/status - Show status\n"
        "/help - Show help"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "Available commands:\n\n"
        "/start\n"
        "/test [count]\n"
        "/status\n"
        "/help\n\n"
        f"UDP destination: {HOST}:{PORT}\n"
        f"Maximum packets per test: {MAX_PACKETS}"
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    with lock:
        total_received = received_packets

    await update.message.reply_text(
        "📊 Status\n\n"
        f"Bot: ONLINE\n"
        f"UDP receiver: "
        f"{'RUNNING' if receiver_running else 'STOPPED'}\n"
        f"Host: {HOST}\n"
        f"Port: {PORT}\n"
        f"Packets received: {total_received}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


async def test(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global received_packets

    count = DEFAULT_PACKETS

    if context.args:
        try:
            count = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ Usage: /test 10"
            )
            return

    if count < 1:
        await update.message.reply_text(
            "❌ Count must be greater than 0."
        )
        return

    if count > MAX_PACKETS:
        await update.message.reply_text(
            f"❌ Maximum allowed count is {MAX_PACKETS}."
        )
        return

    with lock:
        before = received_packets

    await update.message.reply_text(
        f"🧪 UDP test started\n"
        f"Packets: {count}\n"
        f"Destination: {HOST}:{PORT}"
    )

    sent = await asyncio.to_thread(
        udp_test,
        count
    )

    await asyncio.sleep(0.3)

    with lock:
        after = received_packets

    received = after - before
    lost = max(sent - received, 0)

    loss_percent = (
        (lost / sent) * 100
        if sent
        else 0
    )

    await update.message.reply_text(
        "✅ UDP test completed\n\n"
        f"Sent: {sent}\n"
        f"Received: {received}\n"
        f"Missing: {lost}\n"
        f"Loss: {loss_percent:.1f}%\n"
        f"Destination: {HOST}:{PORT}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    receiver_thread = threading.Thread(
        target=udp_receiver,
        daemon=True
    )

    receiver_thread.start()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("status", status)
    )

    app.add_handler(
        CommandHandler("test", test)
    )

    print("🤖 Telegram bot started")
    print(f"UDP receiver listening on {HOST}:{PORT}")

    app.run_polling()


if __name__ == "__main__":
    main()