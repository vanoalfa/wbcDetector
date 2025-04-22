from flask import Flask #Pustaka untuk server flask
from threading import Thread #Pustaka untuk menjalankan bot telegram dan server flask secara bersamaan
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext #Pustaka untuk mengambil komponen yang dibutuhkan bot telegram
#Updater : Untuk menghubungkan bot dengan server Telegram.
#CommandHandler : Untuk perintah /start atau perintah lain yang dikirimkan oleh pengguna.
#MessageHandler : Untuk menangani pesan dari pengguna (contoh: gambar).
#Filters : Untuk menyaring tipe pesan yang diterima (dalam hal ini gambarnya saja).
#CallbackContext : Objek yang menyimpan data konteks saat callback fungsi dipanggil.
from telegram import Update #Pustaka untuk update pesan dari telegram
from detect import detect_white_blood_cells #Mengimpor program deteksi sel darah putih dari file detect.py
from PIL import Image #Pustaka untuk memproses gambar
import os #Pustaka untuk mengakses environment variables

#yang ini untuk konfigurasi botnya teman-teman alterians (telegram)
TOKEN = os.environ.get("API_TELEGRAM") #ngambil API dari telegram

#Message awal
def start(update: Update, context: CallbackContext): #jalan kalau user ketik /start nantinya
    #update:Update untuk menyimpan data pesan dari user telegram
    #context:CallbackContext untuk menyimpan data konteks saat callback fungsi dipanggil dalam hal ini untuk mengirim pesan balasan ke user
    update.message.reply_text("Halo! Kirimkan gambar sel darah putih, dan saya akan beritahu kamu sel apa itu.") #pesan balasan ke user

#udah masuk ke ngurus gambarnya (astagfirullah errornya banyak)
def handle_image(update: Update, context: CallbackContext): #fungsi untuk menangani gambar yang dikirim user
    photo = update.message.photo[-1].get_file() #mengambiil file gambar dari pesan user
    #update.message.photo[-1] : Mengambil gambar terakhir dari pesan yang dikirim user (fungsi dari telegramnya).
    #.get_file() : Mendapatkan file gambar dari objek gambar tersebut.
    file_path = f"static/{photo.file_id}.jpg" #menyimpan gambar di folder static dengan nama file_id.jpg (file_id adalah id gambar yang ditentukan dari telegramnya langsung)
    photo.download(file_path) #download gambar ke folder static

    #Resize gambarnya jadi 640x640 dulu
    update.message.reply_text("Gambar sedang diproses...") #pesan balasan ke user bahwa gambar sedang diproses
    img = Image.open(file_path) #membuka gambar yang sudah di download di folder static. dari pustaka PIL
    img = img.resize((640, 640)) #resize gambar jadi 640x640
    img.save(file_path) #simpan gambar yang sudah di resize

    #ini nanti konek ke detect.py untuk deteksi gambar sell nya
    result_path, result_message = detect_white_blood_cells(file_path) #panggil fungsi detect_white_blood_cells dari file detect.py

    #balik lagi kesini dari detect.py, kirim gambar hasil deteksi ke user
    if result_path: #ambil gambar hasil deteksi dari detect.py
        with open(result_path, 'rb') as result_image: #buka gambar hasil deteksi dari folder static untuk dikirim ke user
        #open(result_path, 'rb'): Membuka file gambar hasil deteksi dari folder static.
        #result_path adalah path dari gambar hasil deteksi yang sudah disimpan di folder static.
        #'rb': Mode baca (read) dalam bentuk biner (binary).
        #as result_image: Menyimpan gambar hasil deteksi ke variabel result_image.
            update.message.reply_photo(photo=result_image, caption=result_message) #kirim gambar hasil deteksi ke user
            #photo=result_image: Gambar hasil deteksi yang sudah dibuka.
            #caption=result_message: Pesan yang akan ditampilkan di bawah gambar hasil deteksi dari detect.py
        os.remove(result_path) #hapus gambar hasil deteksi dari folder static setelah dikirim ke user
    else:
        update.message.reply_text(result_message) #jika tidak ada gambar hasil deteksi, kirim pesan error ke user dan beritahu user bahwa gambar tidak ditemukan
    #result_path: Path dari gambar hasil deteksi yang sudah disimpan di folder static.
    #result_image: Gambar dari file di folder static yang sudah di proses pada fungsi detect_white_blood_cells file detect.py.

#disini main dari program botnya dimana program ini yang akan berjalan untuk menjalankan bot telegram
def start_bot(): #fungsi untuk menjalankan bot telegram
    updater = Updater(TOKEN, use_context=True) #menghubungkan bot dengan server Telegram
    dp = updater.dispatcher #membuat objek dispatcher untuk menangani pesan dari user
    #dp adalah singkatan dari dispatcher yang merupakan objek yang digunakan untuk mengatur dan mengelola handler (fungsi) yang akan dipanggil saat pesan tertentu diterima.
    #updater.dispatcher : Mendapatkan objek dispatcher dari updater.
    #Dispatcher adalah objek yang mengatur dan mengelola handler (fungsi) yang akan dipanggil saat pesan tertentu diterima.
    dp.add_handler(CommandHandler("start", start)) #menambahkan handler untuk perintah /start
    dp.add_handler(MessageHandler(Filters.photo, handle_image)) #Jika user kirim gambar → jalankan handle_image().
    #filters.photo : Menyaring pesan yang hanya berisi gambar.
    #handle_image : Fungsi yang akan dipanggil saat pesan gambar diterima.
    updater.start_polling() #mulai bot telegram
    updater.idle() #membuat bot tetap berjalan sampai diinterupsi secara manual

#Pokoknya ini buat server flasknya
app = Flask(__name__)
#app adalah variabel yang akan digunakan untuk mengakses fungsi-fungsi dari Flask.
#Flask(): adalah fungsi pada pustaka Flask yang digunakan untuk membuat 
#__name__ adalah variabel khusus di Python yang berisi nama modul saat ini. dari refrensi: https://flask.palletsprojects.com/en/2.0.x/quickstart/#a-minimal-application.

@app.route('/') #@app.route('/') adalah decorator yang digunakan untuk menentukan URL yang akan dipetakan ke fungsi home(). refrensinya: https://flask.palletsprojects.com/en/2.0.x/quickstart/#routing
#kenapa '/'? karena ini adalah URL root dari server flask, yaitu URL yang akan dipetakan ke fungsi home() saat server flask dijalankan. misal kalau mau ditambah seperti: '/project' maka nanti urlnya akan membawa ke url halaman projectnya (urlnya akan menjadi https://<nama domain>/project).
def home():
    return "Server WBC detection sedang berjalan, Telegram @WBCDetectorBot dapat digunakan." #tampilan pada browser ketika server flask dijalankan

if __name__ == '__main__': #ini buat menjalankan bot telegram dan server flask secara bersamaan karena __name__ == '__main__' berarti program ini sedang dijalankan sebagai program utama, bukan sebagai modul yang diimpor. diambil dari https://www.geeksforgeeks.org/__name__-special-variable-python/
    Thread(target=start_bot).start() #menjalankan bot telegram
    app.run(host='0.0.0.0', port=5000) #menjalankan server flask di port 5000 dan host 0.0.0.0 agar bisa diakses dari luar (dari internet).
