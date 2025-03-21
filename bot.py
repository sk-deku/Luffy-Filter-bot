import os
import time
import hashlib
from datetime import datetime, timedelta
import requests
import psutil
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask
import threading

# Environment Variables (Set in Koyeb)
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
SHORTENER_KEY = "5a6b57d3cbd44e9b81cda3a2ec9d93024fcc6838"
SHORTENER_API = "https://modijiurl.com/api"

# Initialize Pyrogram Bot
bot = Client("AutoFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB Connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["auto_filter_bot"]
files_collection = db["files"]
users_collection = db["users"]
tokens_collection = db["tokens"]  # New collection for storing tokens

# ======================= [ Start Command ] ======================= #
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Bot is up and running!")

# ======================= [ Verify Tokens ] ======================= #
@bot.on_message(filters.command("verify"))
async def verify_tokens(client, message):
    if message.chat.type != "private":
        await message.reply_text("❌ This command works only in PM.")
        return
    
    user_id = message.from_user.id

    # Check if a valid token exists
    existing_token = tokens_collection.find_one({"user_id": user_id})
    if existing_token:
        expiry_time = existing_token["expiry"]
        if datetime.utcnow() < expiry_time:
            buttons = [
                [InlineKeyboardButton("🤑 Verify & Earn 10 Tokens", url=existing_token["short_link"])],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Earn 10 tokens by verifying this link:", reply_markup=InlineKeyboardMarkup(buttons))
            return
        else:
            # Expire old token
            tokens_collection.delete_one({"user_id": user_id})

    # Generate a new unknown token
    unknown_token = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()[:10]
    original_url = f"https://t.me/Luffy_Anime_Filter_Bot?start=verify_{unknown_token}"

    try:
        response = requests.get(f"{SHORTENER_API}?api={SHORTENER_KEY}&url={original_url}")
        data = response.json()
        if data.get("status") == "success":
            short_link = data["shortenedUrl"]
            expiry_time = datetime.utcnow() + timedelta(hours=1)

            # Store token in database
            tokens_collection.insert_one({"user_id": user_id, "token": unknown_token, "short_link": short_link, "expiry": expiry_time})

            buttons = [
                [InlineKeyboardButton("🤑 Verify & Earn 10 Tokens", url=short_link)],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Earn 10 tokens by verifying this link:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await message.reply_text("❌ Failed to generate short link.")
    except Exception as e:
        await message.reply_text("❌ Error occurred while generating the short link.")
        print(e)

# ======================= [ Token Auto Verification ] ======================= #
@bot.on_message(filters.command("start") & filters.regex(r"verify_(.*)"))
async def verify_start(client, message):
    user_id = message.from_user.id
    token_received = message.text.split("_", 1)[1]

    # Check if token exists and is valid
    token_entry = tokens_collection.find_one({"user_id": user_id, "token": token_received})
    if token_entry:
        # Add 10 tokens to user account
        users_collection.update_one({"user_id": user_id}, {"$inc": {"tokens": 10}}, upsert=True)

        # Delete used token
        tokens_collection.delete_one({"user_id": user_id, "token": token_received})

        await message.reply_text("✅ Token verified! You have received 10 tokens.")
    else:
        await message.reply_text("❌ Invalid or expired token.")

# ======================= [ Link Expired Handling ] ======================= #
@bot.on_message(filters.regex(SHORTENER_API))
async def expired_link_handler(client, message):
    user_id = message.from_user.id
    token_entry = tokens_collection.find_one({"user_id": user_id})
    if token_entry:
        expiry_time = token_entry["expiry"]
        if datetime.utcnow() > expiry_time:
            await message.reply_text("❌ Link expired. Generate a new link using /verify.")
            tokens_collection.delete_one({"user_id": user_id})

# ======================= [ Stats Command ] ======================= #
@bot.on_message(filters.command("stats"))
async def stats(client, message):
    total_files = files_collection.count_documents({})
    total_users = users_collection.count_documents({})

    # Get system storage details
    disk_usage = psutil.disk_usage("/")
    total_space = disk_usage.total // (1024 * 1024)
    used_space = disk_usage.used // (1024 * 1024)
    free_space = disk_usage.free // (1024 * 1024)

    stats_message = (
        f"📊 **Bot Statistics**\n"
        f"📂 **Stored Files:** `{total_files}`\n"
        f"👤 **Total Users:** `{total_users}`\n"
        f"💾 **Used Storage:** `{used_space} MB`\n"
        f"📁 **Free Storage:** `{free_space} MB`\n"
    )

    await message.reply_text(stats_message)

# ======================= [ Health Check (Koyeb) ] ======================= #
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

def run_health_check():
    app.run(host="0.0.0.0", port=8080)

# ======================= [ Bot Start ] ======================= #
if __name__ == "__main__":
    threading.Thread(target=run_health_check, daemon=True).start()
    print("🤖 Bot is running...")
    bot.run()
