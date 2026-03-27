from flask import Flask, render_template, request, send_file
import io, zipfile, os
# استدعاء الدوال من الملفات الأخرى
from pdf_logic import process_pdf_to_images
from excel_logic import download_images_from_excel

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pdf-convert', methods=['GET', 'POST'])
def pdf_convert():
    if request.method == 'POST':
        pdf_files = request.files.getlist('pdf_files')
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for pdf_file in pdf_files:
                base_name = os.path.splitext(pdf_file.filename)[0]
                images = process_pdf_to_images(pdf_file, base_name)
                for img_name, img_content in images:
                    zf.writestr(img_name, img_content)
        memory_file.seek(0)
        return send_file(memory_file, download_name="Baly_PDF_Images.zip", as_attachment=True)
    return render_template('pdf-convert.html')

@app.route('/google-sheets', methods=['GET', 'POST'])
def google_sheets():
    if request.method == 'POST':
        # 1. استلام الملف والبيانات من الفورم
        excel_file = request.files.get('excel_file')
        col_items = request.form.get('item_col')
        col_links = request.form.get('link_col')

        # 2. استدعاء الدالة المسرعة (التي تعيد ملف ZIP جاهز)
        # ملاحظة: دالة download_images_from_excel الآن تعيد BytesIO يحتوي على ZIP
        zip_result = download_images_from_excel(excel_file, col_items, col_links)

        if zip_result:
            # 3. إرسال ملف الـ ZIP مباشرة للمتصفح
            return send_file(
                zip_result, 
                mimetype='application/zip',
                as_attachment=True, 
                download_name="Baly_Excel_Images.zip"
            )
        else:
            return "حدث خطأ أثناء معالجة الملف، يرجى التأكد من أسماء الأعمدة", 400

    return render_template('google-sheets.html')

if __name__ == '__main__':
    app.run(debug=True)