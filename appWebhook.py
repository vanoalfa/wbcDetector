from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from detect import detect_white_blood_cells
from PIL import Image
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
TOKEN = os.getenv("API_TELEGRAM")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Initialize Flask app
app = Flask(__name__)

# Global application object (from python-telegram-bot v20+)
telegram_app = ApplicationBuilder().token(TOKEN).build()

# Command /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirimkan gambar sel darah putih, dan saya akan bantu identifikasi.")

# Image handler
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    file_path = f"static/{photo.file_id}.jpg"
    await photo.download_to_drive(file_path)

    await update.message.reply_text("Gambar sedang diproses...")

    img = Image.open(file_path)
    img = img.resize((640, 640))
    img.save(file_path)

    result_path, result_message = detect_white_blood_cells(file_path)

    if result_path:
        with open(result_path, 'rb') as result_image:
            await update.message.reply_photo(photo=result_image, caption=result_message)
        os.remove(result_path)
    else:
        await update.message.reply_text(result_message)

# Add handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_image))

# Webhook endpoint
@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return 'OK', 200

# Home endpoint
@app.route('/')
def home():
    return "WBC Webhook Server Aktif!"

# Set webhook
@app.before_first_request
def setup_webhook():
    bot = Bot(token=TOKEN)
    url = f"{WEBHOOK_URL}/{TOKEN}"
    asyncio.run(bot.delete_webhook())
    asyncio.run(bot.set_webhook(url=url))

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)