import time
from datetime import datetime, timedelta

# Dictionary to store temporary short links with expiry
short_links = {}

@bot.on_message(filters.command("earn"))
async def earn_tokens(client, message):
    user_id = message.from_user.id

    # Check if a valid short link already exists
    if user_id in short_links:
        link_data = short_links[user_id]
        if datetime.utcnow() < link_data["expiry"]:
            # If the link is still valid, resend it
            buttons = [
                [InlineKeyboardButton("🤑 Earn 10 Tokens", url=link_data["short_link"])],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Earn 10 tokens by bypassing this link:", reply_markup=InlineKeyboardMarkup(buttons))
            return

    # Generate a new tracking URL
    original_url = f"https://yourbot.com/bypass/{user_id}?t={int(time.time())}"

    # Shorten the URL using ModijiURL API
    try:
        response = requests.get(f"{SHORTENER_API}?api={SHORTENER_KEY}&url={original_url}")
        data = response.json()
        if data.get("status") == "success":
            short_link = data["shortenedUrl"]

            # Store the new link with 1-hour expiry
            short_links[user_id] = {
                "short_link": short_link,
                "expiry": datetime.utcnow() + timedelta(hours=1)
            }

            # Send the link as a button
            buttons = [
                [InlineKeyboardButton("🤑 Earn 10 Tokens", url=short_link)],
                [InlineKeyboardButton("📖 How to Verify?", url="https://t.me/LinkZzzg/6")]
            ]
            await message.reply_text("🎉 Earn 10 tokens by bypassing this link:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await message.reply_text("❌ Failed to generate short link. Try again later.")
    except Exception as e:
        await message.reply_text("❌ Error occurred while generating the short link.")
        print(e)
