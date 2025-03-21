import os
import time
import hashlib
import logging
from datetime import datetime, timedelta
import requests
import psutil
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask
import threading

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    user_id = message.from_user.id
    args = message.text.split(" ")
    
    if len(args) > 1 and args[1].startswith("verify_"):
        await verify_start(client, message)
        return
    
    await message.reply_text("✅ Bot is up and running!")

# ======================= [ Verify Tokens ] ======================= #
@bot.on_message(filters.command("verify") & filters.private)
async def verify_tokens(client, message):
    user_id = message.from_user.id
    
    # Remove expired tokens first
    tokens_collection.delete_many({"expiry": {"$lt": datetime.utcnow()}})
    
    # Check if a valid token exists
    existing_token = tokens_collection.find_one({"user_id": user_id})
    if existing_token:
        buttons = [
            [InlineKeyboardButton("🤑 Verify & Earn 10 Tokens", url=existing_token["short_link"])],
            [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
        ]
        await message.reply_text("🎉 Earn 10 tokens by verifying this link:", reply_markup=InlineKeyboardMarkup(buttons))
        return
    
    # Generate a new unknown token
    unknown_token = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()[:10]
    original_url = f"https://t.me/Luffy_Anime_Filter_Bot?start=verify_{unknown_token}"

    try:
        response = requests.get(f"{SHORTENER_API}?api={SHORTENER_KEY}&url={original_url}")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                short_link = data.get("shortenedUrl")
                expiry_time = datetime.utcnow() + timedelta(hours=1)
                tokens_collection.insert_one({"user_id": user_id, "token": unknown_token, "short_link": short_link, "expiry": expiry_time})

                buttons = [
                    [InlineKeyboardButton("🤑 Verify & Earn 10 Tokens", url=short_link)],
                    [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
                ]
                await message.reply_text("🎉 Earn 10 tokens by verifying this link:", reply_markup=InlineKeyboardMarkup(buttons))
            else:
                await message.reply_text("❌ Failed to generate short link.")
        else:
            await message.reply_text("❌ Shortener API error. Please try again later.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Shortener API Error: {e}")
        await message.reply_text("❌ Error occurred while generating the short link.")

# ======================= [ Token Auto Verification ] ======================= #
async def verify_start(client, message):
    user_id = message.from_user.id
    args = message.text.split("_", 1)

    if len(args) < 2:
        await message.reply_text("❌ Invalid verification request.")
        return

    token_received = args[1]
    token_entry = tokens_collection.find_one({"user_id": user_id, "token": token_received})

    if token_entry:
        users_collection.update_one({"user_id": user_id}, {"$inc": {"tokens": 10}}, upsert=True)
        tokens_collection.delete_one({"user_id": user_id, "token": token_received})
        await message.reply_text("✅ Token verified! You have received 10 tokens.")
    else:
        await message.reply_text("❌ Invalid or expired token.")

# ======================= [ File Search ] ======================= #
@bot.on_message(filters.text & filters.group)
async def search_files(client, message):
    query = message.text.lower()
    files = files_collection.find({"filename": {"$regex": query, "$options": "i"}})
    
    file_list = [file["filename"] for file in files]
    if not file_list:
        await message.reply_text("❌ No files found.")
        return

    buttons = [[InlineKeyboardButton(name, callback_data=f"file_{name}")] for name in file_list[:5]]
    buttons.append([InlineKeyboardButton("➡ Next", callback_data="next_page")])
    
    await message.reply_text("📂 **Select a file:**", reply_markup=InlineKeyboardMarkup(buttons))

# ======================= [ File Selection ] ======================= #
@bot.on_callback_query(filters.regex(r"file_(.*)"))
async def file_selection(client, callback_query):
    user_id = callback_query.from_user.id
    file_name = callback_query.data.split("_", 1)[1]
    
    file_path = f"./files/{file_name}"
    if not os.path.exists(file_path):
        await bot.send_message(user_id, "❌ File not found on the server.")
        await callback_query.answer("❌ File is missing!", show_alert=True)
        return
    
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("tokens", 0) > 0:
        users_collection.update_one({"user_id": user_id}, {"$inc": {"tokens": -1}})
        await bot.send_document(user_id, file_path)
        await callback_query.answer("📤 File sent in PM!", show_alert=True)
    else:
        await bot.send_message(user_id, "❌ Not enough tokens! Use /verify to get more tokens.")
        await callback_query.answer("❌ Not enough tokens! Check your PM.", show_alert=True)

# ======================= [ Health Check (Koyeb) ] ======================= #
app = Flask(__name__)
@app.route("/")
def health_check():
    return "Bot is running!", 200

def run_health_check():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# ======================= [ Bot Start ] ======================= #
if __name__ == "__main__":
    threading.Thread(target=run_health_check, daemon=True).start()
    logging.info("🤖 Bot is running...")
    bot.run()
