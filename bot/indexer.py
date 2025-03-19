from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import DB
from bot import app

db = DB()

@app.on_message(filters.channel & (filters.video | filters.document | filters.audio))
async def index_files(client: Client, message: Message):
    """Indexes files from a channel into the database."""
    file = None

    if message.video:
        file = message.video
        file_type = "video"
    elif message.document:
        file = message.document
        file_type = "document"
    elif message.audio:
        file = message.audio
        file_type = "audio"

    if file:
        db.add_file(file.file_id, file.file_name, file.file_size, file_type)
        print(f"Indexed: {file.file_name}")

@app.on_message(filters.command("index") & filters.user(ADMIN_ID))
async def bulk_index(client: Client, message: Message):
    """Indexes all messages in a given channel."""
    if len(message.command) < 2:
        return await message.reply_text("Usage: /index <channel_id>")

    channel_id = message.command[1]
    try:
        async for msg in client.get_chat_history(channel_id):
            if msg.video or msg.document or msg.audio:
                await index_files(client, msg)
        await message.reply_text("Indexing completed.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

