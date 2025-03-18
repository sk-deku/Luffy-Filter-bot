from pyrogram import Client
import logging
from database.db import Database
import os

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

bot = Client("IndexerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = Database(os.getenv("MONGO_URI", ""))

async def index_channel(channel_id):
    try:
        await bot.start()  # Ensure bot session is started
        
        async for message in bot.get_chat_history(channel_id):
            if message.document or message.video or message.audio:
                file_id = message.document.file_id if message.document else \
                          message.video.file_id if message.video else \
                          message.audio.file_id
                file_name = message.document.file_name if message.document else \
                            message.video.file_name if message.video else \
                            message.audio.file_name

                if not db.files.find_one({"file_id": file_id}):  # Prevent duplicate indexing
                    db.add_file(file_id, file_name)

        await bot.stop()  # Stop session properly
        logging.info(f"Indexing completed for {channel_id}")

    except Exception as e:
        logging.error(f"Indexing failed for {channel_id}: {e}")
