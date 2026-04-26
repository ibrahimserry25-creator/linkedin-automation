import os
import time
import sys
from src.database import init_db, save_post

# إصلاح مشكلة طباعة الرموز (الإيموجي) واللغة العربية في الويندوز
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.content_generator import generate_post, generate_image_prompt
from src.image_generator import generate_image

def main():
    print("="*50)
    print("🚀 مدير حسابات التواصل الاجتماعي الآلي 🚀")
    print("="*50)

    # Initialize Database
    init_db()

    # Get input from user
    topic = input("\nأدخل الموضوع أو الفكرة التي تريد الكتابة عنها:\n> ")
    if not topic.strip():
        print("الموضوع لا يمكن أن يكون فارغاً.")
        return

    print("\nاختر المنصة (Platform):")
    print("1. Twitter (ثريد)")
    print("2. LinkedIn (منشور احترافي)")
    choice = input("> ")

    platform = "Twitter" if choice == "1" else "LinkedIn"
    
    print(f"\n⏳ جاري توليد المحتوى لـ {platform}...")
    content = generate_post(topic, platform)
    
    if not content:
        print("❌ حدث خطأ أثناء توليد النص.")
        return
        
    print("\n✅ تم توليد النص بنجاح!")
    print("-"*30)
    print(content)
    print("-"*30)

    print("\n⏳ جاري توليد وصف الصورة باللغة الإنجليزية...")
    img_prompt = generate_image_prompt(topic, content)
    print(f"الوصف المولد: {img_prompt}")

    print("\n⏳ جاري إنشاء الصورة...")
    # Generate a safe filename
    safe_filename = f"post_{int(time.time())}"
    image_path = generate_image(img_prompt, safe_filename)

    if image_path:
         print("✅ تم توليد الصورة بنجاح!")
    
    print("\n⏳ جاري الحفظ في قاعدة البيانات...")
    post_id = save_post(topic, platform, content, image_path)
    
    print(f"\n🎉 تمت العملية بنجاح! تم حفظ المنشور برقم {post_id} في قاعدة البيانات.")
    print("الصورة المحفوظة:", image_path if image_path else "لا توجد صورة")
    print("مستعد للجدولة والنشر اللاحق! 🚀\n")

if __name__ == "__main__":
    main()
