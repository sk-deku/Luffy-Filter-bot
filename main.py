import os
import logging
from pyrogram import Client, filters
from database.db import Database
from utils.shortner import shorten_url
from bot.tokens import add_tokens, deduct_token, get_tokens
from bot.indexer import index_channel
from utils.koyeb_health import health_check

# Load Config
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
PRIVATE_CHANNEL_ID = int(os.getenv("PRIVATE_CHANNEL_ID", 0))
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# Initialize Bot & Database
bot = Client("AutoFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = Database(MONGO_URI)

# Start Command
@bot.on_message(filters.command("start") & filters.private)
def start(client, message):
    message.reply_text("Hello! Send me an anime name to search.")

# Search & Send File
@bot.on_message(filters.text & ~filters.command & filters.private)
def search_files(client, message):
    query = message.text.strip()
    files = db.search_files(query)
    user_id = message.from_user.id
    
    if not files:
        message.reply_text("No files found!")
        return
    
    if get_tokens(user_id) <= 0:  # Ensure 0 tokens are handled safely
        message.reply_text("You need tokens to download files! Bypass a link to earn tokens.")
        return
    
    for file in files:
        try:
            file_id = file.get('file_id')
            if not file_id:
                continue

            short_link = shorten_url(f"https://t.me/{PRIVATE_CHANNEL_ID}/{file_id}")
            if short_link:
                message.reply_text(f"Click here: {short_link}")
                deduct_token(user_id, 1)
            else:
                message.reply_text("Failed to generate short link. Try again later.")
        except Exception as e:
            logging.error(f"Error sending file: {e}")

# Bulk Indexing Command
@bot.on_message(filters.command("index") & filters.user(OWNER_ID))
def index_command(client, message):
    parts = message.text.split(" ")
    if len(parts) < 2:
        message.reply_text("Usage: /index <channel_id>")
        return
    
    channel_id = parts[1]
    try:
        index_channel(channel_id)
        message.reply_text("Indexing complete!")
    except Exception as e:
        logging.error(f"Indexing failed: {e}")
        message.reply_text(f"Indexing failed: {str(e)}")

# Health Check Route (for Koyeb)
@bot.on_message(filters.command("health"))
def health(client, message):
    message.reply_text(health_check())

# Run Bot
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Bot is running...")
    bot.run()
