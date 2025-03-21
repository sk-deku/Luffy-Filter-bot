import os
import time
import hashlib
import logging
from datetime import datetime, timedelta
import requests
import psutil
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from flask import Flask
import threading

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Environment Variables
API_ID = int(os.getenv("API_ID", "0"))  # Default to 0 if not set
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
SHORTENER_KEY = "5a6b57d3cbd44e9b81cda3a2ec9d93024fcc6838"
SHORTENER_API = "https://modijiurl.com/api"

# Initialize Pyrogram Bot
bot = Client("AutoFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB Connection
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["auto_filter_bot"]
    files_collection = db["files"]
    users_collection = db["users"]
    tokens_collection = db["tokens"]
    logging.info("Connected to MongoDB successfully.")
except Exception as e:
    logging.error(f"MongoDB Connection Error: {e}")

# Function to shorten URLs
def shorten_url(url):
    try:
        response = requests.get(f"{SHORTENER_API}?api={SHORTENER_KEY}&url={url}")
        data = response.json()
        return data.get("shortenedUrl", url)
    except Exception as e:
        logging.error(f"URL Shortener Error: {e}")
        return url

# Function to store files from the database channel automatically
@bot.on_message(filters.channel)
def store_files(client, message: Message):
    if message.document or message.video or message.photo:
        file_id = message.document.file_id if message.document else message.video.file_id if message.video else message.photo.file_id
        file_name = message.document.file_name if message.document else "Untitled File"
        
        if files_collection.find_one({"file_id": file_id}):
            logging.info("Duplicate file skipped.")
            return
        
        files_collection.insert_one({"file_id": file_id, "file_name": file_name, "date": datetime.utcnow()})
        logging.info(f"Stored file: {file_name}")

# Command to manually index files from any channel
@bot.on_message(filters.command("index"))
def index_files(client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.document or message.reply_to_message.video or message.reply_to_message.photo):
        message.reply_text("Please reply to a file message from the channel.")
        return
    
    file_id = message.reply_to_message.document.file_id if message.reply_to_message.document else message.reply_to_message.video.file_id if message.reply_to_message.video else message.reply_to_message.photo.file_id
    file_name = message.reply_to_message.document.file_name if message.reply_to_message.document else "Untitled File"
    
    if files_collection.find_one({"file_id": file_id}):
        message.reply_text("This file is already stored.")
        return
    
    files_collection.insert_one({"file_id": file_id, "file_name": file_name, "date": datetime.utcnow()})
    message.reply_text(f"Indexed file: {file_name}")

# Command to show bot statistics
@bot.on_message(filters.command("stats"))
def stats(client, message: Message):
    total_files = files_collection.count_documents({})
    total_users = users_collection.count_documents({})
    db_stats = mongo_client.auto_filter_bot.command("dbStats")
    free_storage = db_stats.get("fsUsedSize", 0)
    used_storage = db_stats.get("dataSize", 0)
    
    stats_text = (f"📊 **Bot Statistics**\n"
                  f"📁 Stored Files: {total_files}\n"
                  f"👤 Total Users: {total_users}\n"
                  f"💾 Used Storage: {used_storage} bytes\n"
                  f"🆓 Free Storage: {free_storage} bytes")
    
    message.reply_text(stats_text)

# Flask App to Keep Bot Alive (If Hosted on Koyeb or Heroku)
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Run Flask in a Separate Thread
threading.Thread(target=run_flask, daemon=True).start()

# Run the bot
bot.run()

