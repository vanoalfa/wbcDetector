import os
from roboflow import Roboflow
from PIL import Image, ImageDraw, ImageFont

#Inisialisasi Roboflow
api_key = os.environ.get("API_ROBOFLOW")
if not api_key:
    raise ValueError("API_ROBOFLOW belum di-set di environment variables!")

rf = Roboflow(api_key=api_key)
project = rf.workspace().project("blood-cell-classification-juuw1")
model = project.version("2").model

#Fungsi untuk mendeteksi sel darah putih, fungsi ini akan dipanggil dari app.py
def detect_white_blood_cells(image_path):
    try:
        #Prediksi gambar
        prediction = model.predict(image_path).json()
        detections = prediction['predictions']

        if len(detections) == 0:
            return None, "Tidak ditemukan sel darah putih pada gambar."

        #Buka gambar asli dari pathnya
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        #font buat tulis teks di bounding box
        try:
            font = ImageFont.truetype("arialbd.ttf", size=22)
        except:
            font = ImageFont.load_default()

        #Hitung jumlah class & total confidence
        class_counts = {}
        total_confidence = 0

        for det in detections:
            class_name = det['class']
            confidence = det['confidence'] * 100  #Dalam bentuk persen
            total_confidence += confidence

            #Hitung jumlah class
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

            #Ambil posisi bounding box
            x, y, w, h = det['x'], det['y'], det['width'], det['height']

            #Konversi ke koordinat box
            left = x - w / 2
            top = y - h / 2
            right = x + w / 2
            bottom = y + h / 2

            #Gambar bounding box
            draw.rectangle([left, top, right, bottom], outline="blue", width=2)

            #Tulis label
            label = f"{class_name} ({confidence:.1f}%)"
            draw.text((left, top - 10), label, fill="blue", font=font)

            #Gambar latar rectangle di belakang teks
            text_bbox = draw.textbbox((0,0), label, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            background_rect = [left, top - text_height - 4, left + text_width + 6, top]
            draw.rectangle(background_rect, fill="blue")

            #Tulis teks lagi di atas kotak
            draw.text((left + 3, top - text_height - 1), label, fill="white", font=font)
            
        avg_confidence = total_confidence / len(detections)

        #Simpan gambar hasil deteksi
        result_path = image_path.replace(".jpg", "_detected.jpg")
        image.save(result_path)

        #Susun pesan hasil deteksi
        result_message = "Sel terdeteksi:\n"
        for class_name, count in class_counts.items():
            result_message += f"- {class_name}: {count} sel\n"

        result_message += f"\nNilai confidence rata-rata: {avg_confidence:.2f}%"

        return result_path, result_message

    except Exception as e:
        return None, f"Terjadi kesalahan saat mendeteksi: {e}"
