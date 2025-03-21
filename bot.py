import os
import time
from datetime import datetime, timedelta
import requests
import psutil
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Environment Variables (Set in Koyeb)
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Channel ID to monitor
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

# ======================= [ Auto Indexing ] ======================= #
@bot.on_message(filters.channel & filters.document)
async def auto_index(client, message: Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    
    if not files_collection.find_one({"file_id": file_id}):
        files_collection.insert_one({"file_id": file_id, "filename": file_name})
        print(f"📂 Indexed: {file_name}")
    
# ======================= [ Manual Indexing ] ======================= #
@bot.on_message(filters.command("index") & filters.group)
async def manual_index(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text("❌ Reply to a document to index it!")
        return
    
    file_id = message.reply_to_message.document.file_id
    file_name = message.reply_to_message.document.file_name
    
    if not files_collection.find_one({"file_id": file_id}):
        files_collection.insert_one({"file_id": file_id, "filename": file_name})
        await message.reply_text(f"✅ Indexed: `{file_name}`")

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
    original_url = f"https://t.me/Luffy_Anime_Filter_Bot?start=earn_{user_id}"
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

# ======================= [ Bot Start ] ======================= #
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.run()
