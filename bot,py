from pyrogram import Client, filters
import os
from database.db import Database
from utils.shortner import shorten_url

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Client("AutoFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = Database(MONGO_URI)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome to the AutoFilter Bot!")

@bot.on_message(filters.command("index") & filters.user(ADMIN_ID))
async def index_channel(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: /index <channel_id>")
        return
    
    channel_id = args[1]
    await message.reply_text(f"Indexing channel: {channel_id}...")
    
    try:
        from bot.indexer import index_channel as index_func
        await index_func(channel_id)
        await message.reply_text(f"Indexing completed for {channel_id}!")
    except Exception as e:
        await message.reply_text(f"Indexing failed: {e}")

@bot.on_message(filters.text)
async def search_files(client, message):
    query = message.text.strip()
    results = db.search_files(query)

    if not results:
        await message.reply_text("No files found.")
        return
    
    user_id = message.from_user.id
    tokens = db.get_tokens(user_id)

    if tokens < len(results):
        await message.reply_text("Not enough tokens! Earn more by bypassing short links.")
        return
    
    reply_text = "Here are your files:\n"
    for file in results:
        short_link = shorten_url(f"https://t.me/{bot.username}?start={file['file_id']}")
        reply_text += f"[{file['file_name']}]({short_link})\n"
    
    db.deduct_token(user_id, len(results))
    await message.reply_text(reply_text, disable_web_page_preview=True)

bot.run()
