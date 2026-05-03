import os
import time
from dotenv import load_dotenv
import json
try:
    from google import genai
except ImportError:
    # Fallback to old library if new one is not installed
    import google.generativeai as genai_old
    genai = None

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def _get_client():
    if genai:
        return genai.Client(api_key=API_KEY)
    return None

def _fallback_post(topic: str, selected_angle: str) -> str:
    # Used when Gemini is down (quota/key/leaked) so Telegram flow still publishes.
    arabic = (
        f"هل بتواجه صعوبة في {topic}؟\n\n"
        f"خلّيني أشاركك 3 خطوات سريعة كبداية (بنفس أسلوب: {selected_angle}):\n"
        f"1) ابدأ بتحديد هدف واضح جدًا خلال 24 ساعة.\n"
        f"2) اختصر الخطة لخطوة واحدة تعملها اليوم.\n"
        f"3) راجع النتائج وكرّر التحسين بدون تعقيد.\n\n"
        f"لو طبّقتها الأسبوع ده، هتلاحظ فرق حقيقي في الأداء. 🚀\n"
        f"سؤالي لك: إيه أصعب خطوة عندك حاليًا في {topic}؟"
    )
    english = (
        f"Are you struggling with {topic}?\n\n"
        "Here are 3 quick steps to start (in the spirit of your chosen angle):\n"
        "1) Define a clear 24-hour goal.\n"
        "2) Reduce the plan to one action you can do today.\n"
        "3) Review results and iterate fast.\n\n"
        "If you try it this week, you’ll see real improvement. 🚀\n"
        f"My question: what’s the hardest step for you right now in {topic}?"
    )
    return arabic + "\n───────────────\n" + english

# Define content angles globally
ANGLES = ["قصة شخصية", "إحصائية صادمة", "نصيحة عملية مباشرة", "مقارنة بين الماضي والحاضر", "خطأ شائع وكيفية تجنبه"]

def generate_post(topic, platform):
    """
    Generates a social media post using the most stable Gemini library.
    """
    import random
    selected_angle = random.choice(ANGLES)

    prompt = f"""
    Write a highly engaging, professional LinkedIn post about: {topic}
    Chosen Angle/Style: {selected_angle}
    
    CRITICAL RULES:
    1. TARGET AUDIENCE: Egyptian professionals.
    2. ARABIC FIRST: Write the entire post in ARABIC first.
    3. SEPARATOR: After the Arabic post, insert: "───────────────"
    4. ENGLISH TRANSLATION: After the separator, write the ENGLISH translation.
    5. THE HOOK: Start with a pattern-interrupting hook.
    6. THE BODY: Use the PAS framework. Keep sentences short.
    7. LENGTH: Concise (max 200 words total).
    8. CALL TO ACTION: End with a thought-provoking question.
    9. Use 2-4 emojis max.
    """

    client = _get_client()
    last_error = None
    if client:
        try:
            print("[*] Trying to generate with google-genai (gemini-flash-latest)...")
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[!] google-genai failed: {e}")
            last_error = e

    # Fallback to old library
    import google.generativeai as g_old
    g_old.configure(api_key=API_KEY)
    for model_name in ['gemini-flash-latest']:
        try:
            print(f"[*] Trying fallback model: {model_name}...")
            model = g_old.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[!] Fallback {model_name} failed: {e}")
            last_error = e
            continue
            
    print(f"[!] Gemini generation failed completely. Using fallback post. Last error: {last_error}")
    return _fallback_post(topic, selected_angle)

def generate_image_prompt(topic, content):
    prompt = f"""
    Create a short English prompt for an AI image generator. Topic: {topic}. 
    STYLE VARIETY (Pick ONE for this prompt):
    - Option A: Photorealistic cinematic photography. High-end lighting (golden hour or studio lighting), 8k, sharp focus, realistic textures, professional camera (Sony A7R IV).
    - Option B: Fine art oil painting. Professional artist style, rich textures, visible brushstrokes, museum quality, expressive and atmospheric.
    
    CRITICAL RULES:
    1. Do NOT include any text, letters, numbers, or writing in the image.
    2. Focus on a clear, single subject related to the topic.
    3. Add these exact keywords at the end: "high quality, 8k resolution, highly detailed, masterpiece, professional composition".
    """
    client = _get_client()
    if client:
        try:
            response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
            return response.text.strip()
        except: pass
    return "3D isometric render representing " + topic + ", modern corporate aesthetic, glowing accents, minimalist, 8k, Unreal Engine 5 style, no text, no humans"

def generate_recommendations(niche="الوظائف، تطوير الذات"):
    prompt = f"Suggest 3 engaging LinkedIn topics for: {niche}. Return ONLY valid JSON: [{{'title': '...', 'angle': '...'}}, ...]"
    client = _get_client()
    if client:
        try:
            response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
            text = response.text.strip()
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except: pass
    return [{"title": "كيف تستخدم الذكاء الاصطناعي", "angle": "نصيحة عملية"}]

def generate_smart_replies(post_text, context="reply"):
    prompt = f"Generate 3 short LinkedIn replies for: {post_text}. Return ONLY valid JSON: [{{'type': '...', 'text': '...'}}, ...]"
    client = _get_client()
    if client:
        try:
            response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
            text = response.text.strip()
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except: pass
    return [{"type": "شكر", "text": "شكراً جزيلاً!"}]
