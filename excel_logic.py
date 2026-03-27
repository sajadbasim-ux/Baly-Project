import pandas as pd
import requests
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_single_image(session, url, clean_name):
    """دالة تحميل صورة واحدة"""
    if 'drive.google.com' in url:
        try:
            file_id = url.split('/d/')[1].split('/')[0] if '/d/' in url else url.split('id=')[1].split('&')[0]
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
        except: return None
    try:
        # إضافة User-Agent لتجنب الحظر
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            return (f"{clean_name}.jpg", response.content)
    except:
        return None
    return None

def download_images_from_excel(file_stream, col_items, col_links):
    """الدالة الرئيسية - متوافقة مع app.py"""
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    try:
        # 1. قراءة الملف وتجهيز المهام
        xl = pd.ExcelFile(file_stream)
        tasks = []
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name)
            df.columns = [str(col).strip() for col in df.columns]
            if col_items in df.columns and col_links in df.columns:
                for _, row in df.iterrows():
                    url, name = str(row[col_links]).strip(), str(row[col_items]).strip()
                    if url.startswith('http') and name != 'nan':
                        clean_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
                        tasks.append((url, clean_name))

        total_files = len(tasks)
        downloaded_images = []
        
        # 2. التحميل المتوازي (سرعة عالية)
        with ThreadPoolExecutor(max_workers=15) as executor:
            future_to_img = {executor.submit(fetch_single_image, session, t[0], t[1]): t for t in tasks}
            
            count = 0
            for future in as_completed(future_to_img):
                count += 1
                result = future.result()
                if result:
                    downloaded_images.append(result)
                
                # طباعة العداد في الكونسول للتأكد من العمل
                print(f"جاري التحميل: {count}/{total_files}") 

        # 3. إنشاء ملف الـ ZIP في الذاكرة
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img_name, img_content in downloaded_images:
                zf.writestr(img_name, img_content)
        zip_buffer.seek(0)
        
        # إرجاع ملف الـ zip (هذا ما يحتاجه app.py)
        return zip_buffer

    except Exception as e:
        print(f"Error: {e}")
        return None