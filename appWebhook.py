import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters, CallbackContext
from detect import detect_white_blood_cells
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Get token and webhook URL from environment
TOKEN = os.getenv("API_TELEGRAM")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# === Handlers ===

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Halo! Kirimkan gambar sel darah putih, dan saya akan bantu identifikasi.")

def handle_image(update: Update, context: CallbackContext):
    photo = update.message.photo[-1].get_file()
    file_path = f"static/{photo.file_id}.jpg"
    photo.download(file_path)

    update.message.reply_text("Gambar sedang diproses...")

    img = Image.open(file_path)
    img = img.resize((640, 640))
    img.save(file_path)

    result_path, result_message = detect_white_blood_cells(file_path)

    if result_path:
        with open(result_path, 'rb') as result_image:
            update.message.reply_photo(photo=result_image, caption=result_message)
        os.remove(result_path)
    else:
        update.message.reply_text(result_message)

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.PHOTO, handle_image))

# === Flask Routes ===

@app.route('/')
def home():
    return "WBC Webhook Server Aktif!", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    if not WEBHOOK_URL or not TOKEN:
        return "Missing environment variable", 500
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    bot.delete_webhook()
    success = bot.set_webhook(url=webhook_url)
    return f"Webhook set: {success}", 200

# === App Export ===
if __name__ == "__main__":
    app.run(debug=True)