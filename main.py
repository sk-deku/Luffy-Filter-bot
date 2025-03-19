import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import DB
from utils.shortener import shorten_url

API_ID = int(os.getenv("API_ID", "12345"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

db = DB()

app = Client("LuffyFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    db.add_user(user_id)
    await message.reply_text("Welcome to Luffy Filter Bot! 🎌")

@app.on_message(filters.command("addfile") & filters.user(ADMIN_ID))
async def add_file(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply_text("Reply to a file to add it.")
    
    file = message.reply_to_message.document
    db.add_file(file.file_id, file.file_name, file.file_size, "document")
    
    await message.reply_text("File added successfully!")

@app.on_message(filters.command("getfile"))
async def get_file(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /getfile <filename>")

    file_name = message.command[1]
    user_id = message.from_user.id

    if db.get_tokens(user_id) <= 0:
        return await message.reply_text("Not enough tokens! Earn or buy tokens.")

    file_data = db.get_file(file_name)
    if file_data:
        db.update_tokens(user_id, -1)
        await message.reply_document(file_data["file_id"])
    else:
        await message.reply_text("File not found.")

@app.on_message(filters.command("shorten"))
async def shorten_url_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /shorten <url>")

    long_url = message.command[1]
    short_url = shorten_url(long_url)

    if short_url:
        await message.reply_text(f"Shortened URL: {short_url}")
    else:
        await message.reply_text("Failed to shorten URL.")

if __name__ == "__main__":
    print("Bot is running...")
    app.run()
