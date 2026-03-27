import pdfplumber
import re
import io
import os

def clean_filename(text):
    """تنظيف النص ليكون صالحاً كاسم ملف ويندوز (مع عكس النص العربي)"""
    if not text: return ""
    # إزالة الرموز الممنوعة
    clean = re.sub(r'[\\/*?:"<>|]', " ", text).strip()
    # عكس النص العربي لكي يظهر بشكل صحيح في أسماء الملفات كما في كودك الأصلي
    return clean[::-1][:100].strip()

def process_pdf_to_images(pdf_file_stream, base_pdf_name):
    """
    تأخذ ملف PDF مرفوع (Stream) وتعيد قائمة بالصور (الاسم، محتوى الصورة)
    """
    extracted_images = []
    
    # فتح ملف الـ PDF من الذاكرة (الذي تم رفعه من المتصفح)
    with pdfplumber.open(pdf_file_stream) as pdf:
        for p_idx, page in enumerate(pdf.pages):
            # 1. استخراج السطور الكاملة والصور
            lines = page.extract_text_lines()
            images = page.images
            
            if not images: continue

            # تحويل الصفحة لصورة عالية الدقة للقص (300 DPI لضمان الجودة)
            page_obj = page.to_image(resolution=300)
            page_image = page_obj.original

            for i, img_obj in enumerate(images):
                img_bbox = (img_obj['x0'], img_obj['top'], img_obj['x1'], img_obj['bottom'])
                
                found_text = ""
                min_distance = 1000 
                
                # 2. البحث عن النص المرتبط (منطق المسافات الخاص بك)
                for line in lines:
                    line_text = line['text'].strip()
                    l_x0, l_top = line['x0'], line['top']
                    
                    img_mid_y = (img_bbox[1] + img_bbox[3]) / 2
                    line_mid_y = (l_top + line['bottom']) / 2
                    
                    dist_y = abs(img_mid_y - line_mid_y)
                    dist_x = abs(img_bbox[2] - l_x0)
                    
                    if dist_y < 30 or (l_top > img_bbox[3] and l_top - img_bbox[3] < 40):
                        if dist_y + (dist_x * 0.5) < min_distance:
                            min_distance = dist_y + (dist_x * 0.5)
                            found_text = line_text

                # 3. تجهيز الاسم النهائي
                final_name = clean_filename(found_text)
                if len(final_name) < 3:
                    final_name = f"{base_pdf_name}_page_{p_idx+1}_img_{i+1}"

                # 4. قص الصورة (Crop)
                scale = page_image.width / page.width
                crop_bbox = (
                    img_bbox[0] * scale, 
                    img_bbox[1] * scale, 
                    img_bbox[2] * scale, 
                    img_bbox[3] * scale
                )
                cropped_img = page_image.crop(crop_bbox)
                
                # 5. حفظ الصورة في الذاكرة بدلاً من الهارد ديسك
                img_io = io.BytesIO()
                cropped_img.save(img_io, "PNG")
                
                # إضافة الصورة للقائمة (اسم الملف، محتوى البايتات)
                extracted_images.append((f"{final_name}.png", img_io.getvalue()))
                
    return extracted_images