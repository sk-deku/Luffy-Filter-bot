import os
import asyncio
import logging
from pyrogram import Client, filters
from pymongo import MongoClient
from fastapi import FastAPI
import uvicorn
from threading import Thread
from bson.objectid import ObjectId

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MONGO_URI = os.getenv("MONGO_URI")
SHORTENER_API = os.getenv("SHORTENER_API")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Initialize MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["AutoFilterBot"]
files_collection = db["files"]
users_collection = db["users"]

# Initialize bot
bot = Client("AutoFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# FastAPI for health check
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "running"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8080)

Thread(target=run_api, daemon=True).start()

# Bot commands
@bot.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("Welcome! Search for files in the group by typing a keyword.")

@bot.on_message(filters.group & filters.text)
def search_files(client, message):
    query = message.text.lower()
    results = list(files_collection.find({"filename": {"$regex": query, "$options": "i"}}))
    
    if not results:
        message.reply_text("No files found.")
        return
    
    buttons = []
    for file in results[:10]:  # Show only first 10 results
        buttons.append([(file["filename"], f"file_{file['_id']}")])
    
    message.reply_text("Select a file:", reply_markup={"inline_keyboard": buttons})

@bot.on_callback_query(filters.regex(r"file_(.*)"))
def handle_callback(client, callback_query):
    file_id = callback_query.data.split("_")[1]
    file_data = files_collection.find_one({"_id": ObjectId(file_id)})
    if file_data:
        user_id = callback_query.from_user.id
        user = users_collection.find_one({"user_id": user_id})
        if user and user.get("tokens", 0) > 0:
            users_collection.update_one({"user_id": user_id}, {"$inc": {"tokens": -1}})
            bot.send_document(user_id, file_data["file_id"], caption="Here's your file.")
        else:
            callback_query.message.reply_text("Not enough tokens. Earn tokens by bypassing a link.")

# Auto-index files when uploaded to channel
@bot.on_message(filters.channel & filters.document)
def save_file(client, message):
    file_data = {
        "filename": message.document.file_name,
        "file_id": message.document.file_id,
        "quality": "720p",  # Extract from filename
        "season": "1",
        "language": "English"
    }
    files_collection.insert_one(file_data)
    message.reply_text(f"✅ File Indexed: {message.document.file_name}")

# Bulk index files from channel
@bot.on_message(filters.command("index") & filters.user(ADMIN_ID))
async def index_channel(client, message):
    count = 0
    async for msg in client.get_chat_history(CHANNEL_ID, limit=100):
        if msg.document:
            file_data = {
                "filename": msg.document.file_name,
                "file_id": msg.document.file_id,
                "quality": "720p",
                "season": "1",
                "language": "English"
            }
            files_collection.insert_one(file_data)
            count += 1
    message.reply_text(f"✅ Indexed {count} files successfully!")

if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
