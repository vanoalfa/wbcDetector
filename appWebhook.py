    from flask import Flask, request
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
    from detect import detect_white_blood_cells  # Fungsi untuk mendeteksi sel darah putih
    from PIL import Image
    import os
    from dotenv import load_dotenv
    import asyncio

    # Load environment variables
    load_dotenv()

    TOKEN = os.getenv("API_TELEGRAM")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    # Flask app
    app = Flask(__name__)

    # Inisialisasi bot dan aplikasi telegram
    bot = Bot(token=TOKEN)
    application = Application.builder().token(TOKEN).build()

    # Handler untuk perintah /start
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Halo! Kirimkan gambar sel darah putih, dan saya akan bantu identifikasi.")

    # Handler untuk gambar
    async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"static/{file.file_id}.jpg"
        await file.download_to_drive(file_path)

        await update.message.reply_text("Gambar sedang diproses...")

        # Proses gambar
        img = Image.open(file_path)
        img = img.resize((640, 640))
        img.save(file_path)

        result_path, result_message = detect_white_blood_cells(file_path)

        if result_path:
            with open(result_path, 'rb') as result_img:
                await update.message.reply_photo(photo=result_img, caption=result_message)
            os.remove(result_path)
        else:
            await update.message.reply_text(result_message)

    # Menambahkan handler ke application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Endpoint root
    @app.route('/')
    def home():
        return "WBC Webhook Server Aktif!"

    # Endpoint webhook
    @app.route(f'/{TOKEN}', methods=['POST'])
    def webhook():
        update = Update.de_json(request.get_json(force=True), bot)
        asyncio.run(application.process_update(update))
        return 'OK', 200

    # Fungsi untuk mengatur webhook
    def setup_webhook():
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        asyncio.run(bot.delete_webhook())
        asyncio.run(bot.set_webhook(url=webhook_url))

    # Jalankan aplikasi
    if __name__ == '__main__':
        setup_webhook()
        app.run(host='0.0.0.0', port=5000)