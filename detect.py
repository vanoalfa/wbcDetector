import os
from roboflow import Roboflow
from PIL import Image, ImageDraw, ImageFont

#Inisialisasi Roboflow
api_key = os.environ.get("API_ROBOFLOW") #Ambil API ROBOFLOW key dari environment variables
if not api_key: #Jika API_ROBOFLOW belum di-set di environment variables, maka akan muncul error
    raise ValueError("API_ROBOFLOW belum di-set di environment variables!") #Error yang akan muncul jika API_ROBOFLOW belum di-set di environment variables

rf = Roboflow(api_key=api_key) #Inisialisasi Roboflow dengan API key yang sudah di-set di environment variables
#rf: variabel yang akan digunakan untuk mengakses fungsi-fungsi dari Roboflow.
project = rf.workspace().project("blood-cell-classification-juuw1") #Ambil project dari Roboflow workspace
model = project.version("2").model #versi model yang digunakan

#Fungsi untuk mendeteksi sel darah putih, fungsi ini akan dipanggil dari app.py
def detect_white_blood_cells(image_path):
    try: #menggunakan try-except untuk menangani error yang mungkin terjadi saat mendeteksi gambar
        #Prediksi gambar
        prediction = model.predict(image_path).json() #Mengirim gambar ke Roboflow untuk diprediksi
        #.json() ditambahkan karena hasil prediksi dari Roboflow adalah dalam bentuk json, jadi harus diubah dulu ke json baru kemudian bisa diproses oleh python.
        detections = prediction['predictions'] #Ambil hasil prediksi dari json yang sudah diubah ke python

        if len(detections) == 0: #Jika tidak ada sel darah putih yang terdeteksi
            return None, "Tidak ditemukan sel darah putih pada gambar." #maka akan mengirimkan pesan ke user bahwa tidak ada sel darah putih yang terdeteksi

        #Buka gambar asli dari pathnya
        image = Image.open(image_path) #Membuka gambar yang sudah di download di folder static. dari pustaka PIL
        draw = ImageDraw.Draw(image) #Membuat variabel ImageDraw untuk memberikan visualisasi pada gambar

        #font buat tulis teks di bounding box
        try:
            font = ImageFont.truetype("arialbd.ttf", size=22) #Coba gunakan font Arial Bold
        except:
            font = ImageFont.load_default() #Jika font Arial Bold tidak ditemukan, gunakan font default yang ada di PIL

        #Hitung jumlah class & total confidence
        class_counts = {} #Dictionary untuk menghitung jumlah class
        total_confidence = 0 #variabel untuk menghitung total confidence, = 0 karena pada awalnya belum ada confidence yang dihitung.

        for det in detections: #Looping untuk setiap deteksi sel yang ada di gambar
            class_name = det['class'] #ambil nama class dari roboflow
            #det['class']: Nama class dari deteksi sel yang ada di gambar, diambil dari json yang sudah diubah ke python.]
            confidence = det['confidence'] * 100  #Ubah confidence dari desimal ke persen
            total_confidence += confidence #Tambahkan confidence ke total confidence

            #Hitung jumlah class
            class_counts[class_name] = class_counts.get(class_name, 0) + 1 #Tambahkan jumlah class ke dictionary class_counts

            #Ambil posisi bounding box
            x, y, w, h = det['x'], det['y'], det['width'], det['height'] #Ambil posisi bounding box dari roboflow

            #Konversi ke koordinat box
            left = x - w / 2 #Koordinat kiri bounding box
            top = y - h / 2 #Koordinat atas bounding box
            right = x + w / 2 #Koordinat kanan bounding box
            bottom = y + h / 2 #Koordinat bawah bounding box

            #Gambar bounding box
            draw.rectangle([left, top, right, bottom], outline="blue", width=2) #Gambar bounding box di gambar yang sudah di download di folder static dan sudah di deteksi

            #Tulis label
            label = f"{class_name} ({confidence:.1f}%)" #Label yang akan ditulis di bounding box
            #class_name: Nama class dari deteksi sel yang ada di gambar, diambil dari json yang sudah diubah ke python.
            #confidence:.1f: Confidence dari deteksi sel yang ada di gambar, diambil dari json yang sudah diubah ke python.
            #.1f: Format angka desimal dengan 1 angka di belakang koma.
            draw.text((left, top - 10), label, fill="blue", font=font) #Tulis label di bounding box
            #(left, top - 10): Koordinat teks yang akan ditulis di bounding box.
            #-10: Jarak antara teks dan bounding box.
            #label: Label yang akan ditulis di bounding box dan sudah di set sebelumnya.
            #fill="blue": Warna teks.
            #font=font: Font yang akan digunakan untuk menulis teks.
            #font: Font yang sudah di-set di atas.
            
            #Gambar latar rectangle di belakang teks
            text_bbox = draw.textbbox((0,0), label, font=font) #Ambil bounding box dari teks
            #draw.textbbox((0,0), label, font=font): Mengambil bounding box dari teks yang akan ditulis di bounding box.
            #draw: Variabel ImageDraw yang sudah di-set sebelumnya pada line 28
            #textbbox: pustaka PIL untuk mengambil bounding box dari teks.
            text_width = text_bbox[2] - text_bbox[0] #Lebar teks
            #text_bbox[2]: angka 2 adalah koordinat kanan dari bounding box teks.
            #text_bbox[0]: angka 0 adalah koordinat kiri dari bounding box teks.
            text_height = text_bbox[3] - text_bbox[1]
            #text_bbox[3]: angka 3 adalah koordinat bawah dari bounding box teks.
            #text_bbox[1]: angka 1 adalah koordinat atas dari bounding box teks.
            #refrensi: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.textbbox    
            background_rect = [left, top - text_height - 4, left + text_width + 6, top] #variabel kotak untuk latar teks
            draw.rectangle(background_rect, fill="blue") #Gambar kotak untuk latar teks
            draw.text((left + 3, top - text_height - 1), label, fill="white", font=font) #tulis teks di atas kotak background_rect
            
        avg_confidence = total_confidence / len(detections) #Hitung rata-rata confidence
        #total_confidence: Total confidence dari semua deteksi sel yang ada di gambar.
        #len(detections): Jumlah deteksi sel yang ada di gambar.
        
        #Simpan gambar hasil deteksi
        result_path = image_path.replace(".jpg", "_detected.jpg") #Ganti nama file gambar hasil deteksi dengan menambahkan "_detected" di belakang nama file asli. sebagai contoh: 123.jpg menjadi 123_detected.jpg
        #.replace merupakan fungsi dari python untuk mengganti string dengan string lain. refrensinya: https://www.w3schools.com/python/ref_string_replace.asp
        image.save(result_path) #Simpan gambar hasil deteksi di folder static

        #Susun pesan hasil deteksi
        result_message = "Sel terdeteksi:\n" #Pesan yang akan dikirim ke user
        for class_name, count in class_counts.items(): #Looping untuk setiap class yang ada di dictionary class_counts
            result_message += f"> {class_name}: {count} sel\n" #Tambahkan jumlah class ke pesan yang akan dikirim ke user. jadi nanti muncul diusernya seperti: - Eosinophil: 1 sel, > Lymphocyte: 2 sel

        result_message += f"\nNilai confidence rata-rata: {avg_confidence:.2f}%" #Tambahkan rata-rata confidence ke pesan yang akan dikirim ke user. nanti munculnya seperti: Nilai confidence rata-rata: 95.00%

        return result_path, result_message #Kembalikan path gambar hasil deteksi dan pesan hasil deteksi ke app.py
        #result_path: Path dari gambar hasil deteksi yang sudah disimpan di folder static.
        #result_message: Pesan yang akan dikirim ke user.

    except Exception as e:
        return None, f"Terjadi kesalahan saat mendeteksi: {e}" #Jika terjadi error saat mendeteksi gambar, maka akan mengirimkan pesan error ke user dan beritahu user bahwa terjadi kesalahan saat mendeteksi gambar. misalnya: Terjadi kesalahan saat mendeteksi: [Errno 2] No such file or directory: 'static/123.jpg'
