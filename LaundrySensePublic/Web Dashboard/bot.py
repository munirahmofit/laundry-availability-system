import telebot
import firebase_admin
from firebase_admin import credentials, db
import threading
import time
import glob
import os

# ---- TELEGRAM CONFIG ----
BOT_TOKEN = "*************************"

# ---- FIREBASE INIT ----
json_files = [f for f in glob.glob("*.json") if f != "firebase.json" and "adminsdk" in f]
if not json_files:
    print("ERROR: Service account JSON not found!")
    print("Make sure the adminsdk JSON file is in this folder.")
    exit()

cred = credentials.Certificate(json_files[0])
firebase_admin.initialize_app(cred, {
    "databaseURL": "******************************"
})
print(f"Firebase connected using: {json_files[0]}")

# ---- TELEBOT INIT ----
bot = telebot.TeleBot(BOT_TOKEN)

# ---- LAUNDRY & MACHINE CONFIG ----
LAUNDRIES = ["LaundryA", "LaundryB", "LaundryC"]
MACHINES  = ["Machine1", "Machine2", "Machine3"]

# Display names matching dashboard
LAUNDRY_NAMES = {
    "LaundryA": "LaundryLab",
    "LaundryB": "BubbleLab",
    "LaundryC": "LaundryBar"
}

# ---- DATA STORES ----
waiting_users = {}   # { "LaundryA_Machine1": [chat_id1, chat_id2] }
last_status   = {}   # { "LaundryA_Machine1": "Available" }
last_notified = {}   # { "LaundryA_Machine1": timestamp } — cooldown

# ---- BOT COMMANDS ----
@bot.message_handler(commands=["start"])
def handle_start(message):
    chat_id = message.chat.id
    text    = message.text.strip()
    parts   = text.split()

    if len(parts) > 1:
        payload = parts[1]  # e.g. LaundryA_Machine1
        valid_keys = [f"{l}_{m}" for l in LAUNDRIES for m in MACHINES]

        if payload in valid_keys:
            # Register user for this machine
            if payload not in waiting_users:
                waiting_users[payload] = []
            if chat_id not in waiting_users[payload]:
                waiting_users[payload].append(chat_id)

            laundry_key = payload.split("_")[0]
            machine_key = payload.split("_")[1]

            # Use display names
            laundry_name = LAUNDRY_NAMES.get(laundry_key, laundry_key)
            machine_name = machine_key.replace("Machine", "Machine ")

            bot.send_message(
                chat_id,
                f"✅ Got it! I'll notify you when {machine_name} "
                f"at {laundry_name} is done.\n\n"
                f"You can close this chat now — I'll message you "
                f"when your laundry is ready! 👕"
            )
            print(f"User {chat_id} registered for {payload}")
            return

    # Normal /start — no payload
    bot.send_message(
        chat_id,
        "👋 Welcome to LaundrySense Bot!\n\n"
        "To get notified when your laundry is done:\n"
        "1. Open the LaundrySense dashboard\n"
        "2. Find your machine (In Use)\n"
        "3. Tap 🔔 Notify Me\n\n"
        "I'll message you when the machine is finished! 🧺"
    )

@bot.message_handler(func=lambda m: True)
def handle_any(message):
    bot.send_message(
        message.chat.id,
        "To get notified, please tap 🔔 Notify Me "
        "on the LaundrySense dashboard.\n\n"
        "🌐 https://laundrysense-52659.web.app"
    )

# ---- NOTIFY USERS ----
def notify_users(key, laundry, machine):
    users = waiting_users.get(key, [])
    if not users:
        return

    # Use display names
    laundry_name = LAUNDRY_NAMES.get(laundry, laundry)
    machine_name = machine.replace("Machine", "Machine ")

    for chat_id in users:
        try:
            bot.send_message(
                chat_id,
                f"✅ Your laundry is DONE!\n\n"
                f"📍 {laundry_name}\n"
                f"🫧 {machine_name} is now Available\n\n"
                f"Please collect your clothes now 👕",
                timeout=10
            )
            print(f"Notified user {chat_id} for {key}")
        except Exception as e:
            print(f"Failed to notify {chat_id}: {e}")
            return  # retry next cycle if failed

    # Clear waiting list after successful notification
    waiting_users[key] = []

# ---- FIREBASE MONITOR ----
def monitor_firebase():
    print("Monitoring Firebase for machine status changes...")
    while True:
        try:
            for laundry in LAUNDRIES:
                for machine in MACHINES:
                    key = f"{laundry}_{machine}"
                    ref = db.reference(f"/{laundry}/{machine}/status")
                    status = ref.get()

                    if status is None:
                        status = "Available"

                    prev = last_status.get(key)

                    # Detect In Use → Available
                    if prev == "In Use" and status == "Available":
                        current_time = time.time()
                        last_time    = last_notified.get(key, 0)

                        # 60 second cooldown per machine
                        if current_time - last_time > 60:
                            print(f"Machine done: {key}")
                            notify_users(key, laundry, machine)
                            last_notified[key] = current_time
                        else:
                            print(f"Skipped {key} — cooldown active")

                    last_status[key] = status

        except Exception as e:
            print(f"Firebase error: {e}")

        time.sleep(10)  # check every 10 seconds

# ---- MAIN ----
print("LaundrySense Bot is running...")
print("Waiting for users to press Notify Me...")

# Run Firebase monitor in background thread
monitor_thread = threading.Thread(target=monitor_firebase, daemon=True)
monitor_thread.start()

# Run Telegram bot
bot.infinity_polling()