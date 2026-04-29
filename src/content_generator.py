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
    if client:
        try:
            print("[*] Trying to generate with google-genai (gemini-1.5-flash)...")
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[!] google-genai failed: {e}")

    # Fallback to old library
    import google.generativeai as g_old
    g_old.configure(api_key=API_KEY)
    for model_name in ['gemini-1.5-flash', 'gemini-pro', 'models/gemini-pro']:
        try:
            print(f"[*] Trying fallback model: {model_name}...")
            model = g_old.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[!] Fallback {model_name} failed: {e}")
            continue
            
    return None

def generate_image_prompt(topic, content):
    prompt = f"Create a short English prompt for an AI image generator. Topic: {topic}. Style: Professional candid photography, Unsplash style."
    client = _get_client()
    if client:
        try:
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            return response.text.strip()
        except: pass
    return "professional illustration of " + topic

def generate_recommendations(niche="الوظائف، تطوير الذات"):
    prompt = f"Suggest 3 engaging LinkedIn topics for: {niche}. Return ONLY valid JSON: [{{'title': '...', 'angle': '...'}}, ...]"
    client = _get_client()
    if client:
        try:
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
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
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            text = response.text.strip()
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except: pass
    return [{"type": "شكر", "text": "شكراً جزيلاً!"}]
