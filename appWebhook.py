from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
from detect import detect_white_blood_cells  # Fungsi untuk mendeteksi sel darah putih
from PIL import Image
import os
from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi Flask app
app = Flask(__name__)

# Ambil token dan URL webhook dari environment variables
TOKEN = os.getenv("API_TELEGRAM")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Inisialisasi bot dan dispatcher
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# Fungsi command /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Halo! Kirimkan gambar sel darah putih, dan saya akan bantu identifikasi.")

# Fungsi untuk menangani gambar
def handle_image(update: Update, context: CallbackContext):
    # Ambil gambar yang dikirimkan
    photo = update.message.photo[-1].get_file()
    file_path = f"static/{photo.file_id}.jpg"
    photo.download(file_path)

    update.message.reply_text("Gambar sedang diproses...")

    # Buka dan ubah ukuran gambar untuk memprosesnya
    img = Image.open(file_path)
    img = img.resize((640, 640))  # Resize gambar menjadi 640x640
    img.save(file_path)

    # Panggil fungsi deteksi sel darah putih
    result_path, result_message = detect_white_blood_cells(file_path)

    # Kirim hasil deteksi kembali ke pengguna
    if result_path:
        with open(result_path, 'rb') as result_image:
            update.message.reply_photo(photo=result_image, caption=result_message)
        os.remove(result_path)  # Hapus gambar sementara
    else:
        update.message.reply_text(result_message)  # Kirim pesan jika tidak ada hasil

# Tambahkan handler ke dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.photo, handle_image))

# Endpoint root
@app.route('/')
def home():
    return "WBC Webhook Server Aktif!"

# Endpoint webhook dari Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK', 200

# Setup webhook saat pertama kali dijalankan
def setup_webhook():
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    bot.delete_webhook()  # Hapus webhook sebelumnya jika ada
    bot.set_webhook(url=webhook_url)  # Set webhook baru

# Jalankan aplikasi Flask
if __name__ == '__main__':
    setup_webhook()  # Panggil fungsi setup webhook sebelum menjalankan app
    app.run(host='0.0.0.0', port=5000, debug=False)