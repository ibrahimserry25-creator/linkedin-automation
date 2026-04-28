import sys
import os
from datetime import datetime

# استدعاء المتغيرات من ملفك الأصلي
sys.path.insert(0, os.path.dirname(__file__))
from standalone_scheduler import POST_HOURS

print("="*60)
print("🕒 أداة محاكاة جدول تشغيل البوستات (بالتوقيت المحلي - القاهرة)")
print(f"📌 الساعات المبرمجة للنشر في الكود: {POST_HOURS}")
print("="*60)

# أوقات تشغيل GitHub Actions بناءً على الكرون (0 6,12 * * *)
github_cron_utc = [6, 12]
github_cron_cairo = [utc + 3 for utc in github_cron_utc]

print(f"\n⚙️ 1. فحص إعدادات GitHub Actions (الملف scheduler.yml):")
print(f"   الكرون مبرمج يشتغل في أوقات UTC: {github_cron_utc}")
print(f"   بما يعادل توقيت القاهرة (UTC+3): {github_cron_cairo}")

if github_cron_cairo == POST_HOURS:
    print("   ✅ إعدادات GitHub Actions مطابقة تماماً لساعات بايثون المبرمجة!")
else:
    print("   ❌ يوجد اختلاف بين GitHub Actions وبايثون!")

print("\n🚀 2. محاكاة عمل النظام (standalone_scheduler.py) على مدار الـ 24 ساعة:")
print("-" * 60)

posts_generated = 0
for hour in range(24):
    for minute in [0, 5, 30]: # الدقيقة 0 هي التي يعمل فيها GitHub Actions، باقي الدقائق هي لمحاكاة تليجرام
        # دي نفس الشروط اللي موجودة في الكود بتاعك بالظبط
        is_webhook = (minute == 5) # نفترض أن هناك رسالة تليجرام في الدقيقة 5
        will_publish = hour in POST_HOURS and minute < 10 and not is_webhook
        
        time_str = f"{hour:02d}:{minute:02d}"
        
        if is_webhook:
            print(f"⏰ {time_str} -> 👤 رسالة تليجرام! (لن يتم نشر البوست التلقائي بسبب وجود أمر مباشر)")
        elif will_publish:
            print(f"⏰ {time_str} -> 🟢 يتم النشر التلقائي الآن! (ينطبق الشرط: الساعة {hour} والدقيقة < 10)")
            posts_generated += 1
        else:
            # عشان الزحمة، هنطبع بس الساعات اللي مفروض ينشر فيها بس الدقيقة غلط عشان نتأكد إنه مش هيكرر
            if hour in POST_HOURS and minute >= 10:
                print(f"⏰ {time_str} -> 🔴 لن يتم النشر (الشرط لم يتحقق: الدقيقة {minute} أكبر من 10)")

print("-" * 60)
print(f"📊 النتيجة النهائية: النظام سيقوم بنشر {posts_generated} بوستات تلقائية في اليوم.")
if posts_generated == 2:
    print("✅ المحاكاة ناجحة 100%! الجدول يعمل كما هو متوقع: بوست الساعة 9 صباحاً وبوست الساعة 3 عصراً.")
else:
    print("❌ هناك خطأ في المحاكاة، يرجى المراجعة.")
