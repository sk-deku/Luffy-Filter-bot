import os
import time
from datetime import datetime, timedelta
import requests
import psutil
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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

# ======================= [ Start Command ] ======================= #
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Bot is up and running!")

# ======================= [ File Search ] ======================= #
@bot.on_message(filters.text & filters.group)
async def search_files(client, message):
    query = message.text.lower()
    files = files_collection.find({"filename": {"$regex": query, "$options": "i"}})

    file_list = []
    for file in files:
        file_list.append(file["filename"])

    if not file_list:
        await message.reply_text("❌ No files found.")
        return

    buttons = [[InlineKeyboardButton(f"{name}", callback_data=f"file_{name}")] for name in file_list[:5]]
    buttons.append([InlineKeyboardButton("➡ Next", callback_data="next_page")])

    await message.reply_text("📂 **Select a file:**", reply_markup=InlineKeyboardMarkup(buttons))

# ======================= [ File Selection ] ======================= #
@bot.on_callback_query(filters.regex(r"file_(.*)"))
async def file_selection(client, callback_query):
    user_id = callback_query.from_user.id
    file_name = callback_query.data.split("_", 1)[1]

    # Check if user has enough tokens
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("tokens", 0) > 0:
        users_collection.update_one({"user_id": user_id}, {"$inc": {"tokens": -1}})
        await bot.send_document(user_id, f"./files/{file_name}")
        await callback_query.answer("📤 File sent in PM!", show_alert=True)
    else:
        await bot.send_message(user_id, "❌ Not enough tokens! Use /earn to get more tokens.")
        await callback_query.answer("❌ Not enough tokens! Check your PM.", show_alert=True)

# ======================= [ Earn Tokens ] ======================= #
@bot.on_message(filters.command("earn"))
async def earn_tokens(client, message):
    user_id = message.from_user.id

    # Check if a valid short link exists
    if user_id in short_links:
        link_data = short_links[user_id]
        if datetime.utcnow() < link_data["expiry"]:
            buttons = [
                [InlineKeyboardButton("🤑 Earn 10 Tokens", url=link_data["short_link"])],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Earn 10 tokens by bypassing this link:", reply_markup=InlineKeyboardMarkup(buttons))
            return

    # Generate new short link
    original_url = f"https://yourbot.com/bypass/{user_id}?t={int(time.time())}"
    try:
        response = requests.get(f"{SHORTENER_API}?api={SHORTENER_KEY}&url={original_url}")
        data = response.json()
        if data.get("status") == "success":
            short_link = data["shortenedUrl"]
            short_links[user_id] = {"short_link": short_link, "expiry": datetime.utcnow() + timedelta(hours=1)}

            buttons = [
                [InlineKeyboardButton("🤑 Earn 10 Tokens", url=short_link)],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Earn 10 tokens by bypassing this link:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await message.reply_text("❌ Failed to generate short link.")
    except Exception as e:
        await message.reply_text("❌ Error occurred while generating the short link.")
        print(e)

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
@bot.on_message(filters.command("health"))
async def health_check(client, message):
    await message.reply_text("✅ Bot is running healthy!")

# ======================= [ Bot Start ] ======================= #
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.run()
