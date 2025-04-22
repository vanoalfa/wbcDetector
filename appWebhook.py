    from flask import Flask, request
    from telegram import Bot, Update
    from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
    from detect import detect_white_blood_cells
    from PIL import Image
    import os

    # Inisialisasi Flask app
    app = Flask(__name__)

    # Ambil token dari environment variable
    TOKEN = os.environ.get("API_TELEGRAM")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Contoh: https://wbc-detector.up.railway.app

    # Inisialisasi bot dan dispatcher
    bot = Bot(token=TOKEN)
    dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

    # Fungsi command /start
    def start(update: Update, context: CallbackContext):
        update.message.reply_text("Halo! Kirimkan gambar sel darah putih, dan saya akan bantu identifikasi.")

    # Fungsi untuk menangani gambar
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
    @app.before_first_request
    def setup_webhook():
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        bot.delete_webhook()
        bot.set_webhook(url=webhook_url)

    # Run Flask
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
