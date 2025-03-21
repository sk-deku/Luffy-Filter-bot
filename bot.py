import os
import time
import random
import string
from datetime import datetime, timedelta
import requests
import psutil
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask, request
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

# Store temporary short links with expiry
short_links = {}

# ======================= [ Verify Tokens Command ] ======================= #
@bot.on_message(filters.command("verify"))
async def verify_tokens(client, message):
    if message.chat.type != "private":
        await message.reply_text("❌ This command works only in PM.")
        return

    user_id = message.from_user.id

    # Check if a valid short link exists
    if user_id in short_links:
        link_data = short_links[user_id]
        if datetime.utcnow() < link_data["expiry"]:
            buttons = [
                [InlineKeyboardButton("🤑 Verify & Earn 10 Tokens", url=link_data["short_link"])],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Click below to verify & earn 10 tokens:", reply_markup=InlineKeyboardMarkup(buttons))
            return

    # Generate new unique token
    unique_token = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    original_url = f"https://t.me/Luffy_Anime_Filter_Bot?start=verify_{unique_token}"

    try:
        response = requests.get(f"{SHORTENER_API}?api={SHORTENER_KEY}&url={original_url}")
        data = response.json()
        if data.get("status") == "success":
            short_link = data["shortenedUrl"]
            short_links[user_id] = {
                "short_link": short_link,
                "token": unique_token,
                "expiry": datetime.utcnow() + timedelta(hours=1),
                "earned": False
            }

            buttons = [
                [InlineKeyboardButton("🤑 Verify & Earn 10 Tokens", url=short_link)],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Click below to verify & earn 10 tokens:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await message.reply_text("❌ Failed to generate short link.")
    except Exception as e:
        await message.reply_text("❌ Error occurred while generating the short link.")
        print(e)

# ======================= [ Webhook for Token Verification ] ======================= #
app = Flask(__name__)

@app.route("/verify", methods=["GET"])
def verify():
    token = request.args.get("token")
    user_id = request.args.get("user_id")

    if not token or not user_id:
        return "Invalid request.", 400

    user_id = int(user_id)

    if user_id not in short_links:
        return "❌ Link Expired.", 200

    link_data = short_links[user_id]
    if datetime.utcnow() > link_data["expiry"]:
        del short_links[user_id]
        return "❌ Link Expired.", 200

    if link_data["earned"]:
        return "❌ Tokens already claimed.", 200

    # Add 10 tokens to the user's account
    users_collection.update_one({"user_id": user_id}, {"$inc": {"tokens": 10}}, upsert=True)
    short_links[user_id]["earned"] = True
    return "✅ Tokens Added.", 200

def run_health_check():
    app.run(host="0.0.0.0", port=8080)

# ======================= [ Bot Start ] ======================= #
if __name__ == "__main__":
    threading.Thread(target=run_health_check, daemon=True).start()
    print("🤖 Bot is running...")
    bot.run()
