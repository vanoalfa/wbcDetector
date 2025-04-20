from flask import Flask
from threading import Thread
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
from detect import detect_white_blood_cells
from PIL import Image
import os

#yang ini untuk konfigurasi botnya teman-teman alterians (telegram)
TOKEN = os.environ.get("API_TELEGRAM")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Halo! Kirimkan gambar sel darah putih, dan saya akan deteksi.")


#udah masuk ke ngurus gambarnya (astagfirullah errornya banyak)
def handle_image(update: Update, context: CallbackContext):
    photo = update.message.photo[-1].get_file()
    file_path = f"static/{photo.file_id}.jpg"
    photo.download(file_path)

    #Resize gambarnya jadi 640x640 dulu bolo
    img = Image.open(file_path)
    img = img.resize((640, 640))
    img.save(file_path)
    update.message.reply_text("Gambar sedang diproses...")

    #ini nanti konek ke detect.py untuk deteksi gambar sell nya
    result_path, result_message = detect_white_blood_cells(file_path)

    #balik lagi kesini dari detect.py, kirim gambar hasil deteksi ke user
    if result_path:
        with open(result_path, 'rb') as result_image:
            update.message.reply_photo(photo=result_image, caption=result_message)
    else:
        update.message.reply_text(result_message)

def start_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()

#Pokoknya ini buat nampilin server flasknya berjalan
app = Flask(__name__)

@app.route('/')
def home():
    return "Server WBC detection sedang berjalan, Telegram @WBCDetectorBot dapat digunakan."

if __name__ == '__main__':
    Thread(target=start_bot).start()
    app.run(host='0.0.0.0', port=5000) 
