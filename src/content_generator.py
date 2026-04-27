import os
import time
from dotenv import load_dotenv
import json
import google.generativeai as genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the old stable library
genai.configure(api_key=API_KEY)

# Define content angles globally
ANGLES = ["قصة شخصية", "إحصائية صادمة", "نصيحة عملية مباشرة", "مقارنة بين الماضي والحاضر", "خطأ شائع وكيفية تجنبه"]

def generate_post(topic, platform):
    """
    Generates a social media post using the most stable Gemini library.
    """
    import random
    selected_angle = random.choice(ANGLES)

    if platform.lower() == "twitter":
        prompt = f"اكتب تغريدة احترافية عن: {topic}. الزاوية: {selected_angle}. القواعد: قصيرة، إيموجي واحد، لا تزد عن 280 حرف."
    else:
        prompt = f"""
        Write a highly engaging, professional LinkedIn post about: {topic}
        Chosen Angle/Style: {selected_angle}
        
        CRITICAL RULES (Applying Behavioral Psychology):
        1. BILINGUAL POST: You MUST write the entire post in ENGLISH first.
        2. SEPARATOR: After the English post, insert a separator line (e.g., "───────────────").
        3. ARABIC TRANSLATION: After the separator, write the exact ARABIC translation.
        4. THE HOOK (Attention): Start with a pattern-interrupting hook using curiosity, a bold claim, or a relatable pain point (FOMO).
        5. THE BODY (Desire & Value): Use the PAS framework (Problem-Agitate-Solution) or AIDA. Keep sentences short, punchy, and use white space for easy scanning.
        6. LENGTH: Keep it concise (max 200 words total for both languages combined).
        7. CALL TO ACTION (Action): End the post with an open-ended, thought-provoking question to trigger the psychology of reciprocity and encourage comments (in both languages).
        """

    # List of models to try using the stable library
    models_to_try = [
        'gemini-flash-latest', 
        'gemini-2.5-flash-lite', 
        'gemini-pro-latest',
        'gemini-3-flash-preview'
    ]
    
    for model_name in models_to_try:
        try:
            print(f"[*] Trying to generate with {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[!] {model_name} failed: {e}")
            continue
            
    return None

def generate_image_prompt(topic, content):
    """
    Generates an image prompt using the stable library.
    """
    prompt = f"Create a short, descriptive English prompt for an AI image generator. Topic: {topic}. Style: Highly realistic candid photography, natural lighting, shot on 35mm lens, Unsplash style, professional, no text, no cartoons, no fake 3D look."
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "professional illustration of " + topic

def generate_recommendations(niche="الوظائف، مقابلات العمل، التكنولوجيا، الذكاء الاصطناعي، مشاكل العمل، تطوير الذات، وكيفية الحصول على ترقية"):
    """
    Generates 3 trending and engaging post ideas for the given niche.
    Returns a JSON string containing an array of objects with 'title' and 'angle'.
    """
    prompt = f"""
    You are an expert LinkedIn content strategist.
    Suggest 3 highly engaging, trending topics to write about today for the niche: "{niche}".
    For each topic, provide a short, catchy Title (Arabic) and a recommended Angle/Hook (Arabic).
    
    IMPORTANT: You MUST return ONLY valid JSON in the following format:
    [
        {{"title": "...", "angle": "..."}},
        {{"title": "...", "angle": "..."}},
        {{"title": "...", "angle": "..."}}
    ]
    Do not include markdown formatting like ```json or any other text.
    """
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print(f"[!] Error generating recommendations: {e}")
        # Fallback recommendations if API fails
        return [
            {"title": "كيف تستخدم الذكاء الاصطناعي في عملك اليومي", "angle": "مقارنة بين الماضي والحاضر"},
            {"title": "أكبر خطأ مهني ارتكبته وكيف تعلمت منه", "angle": "قصة شخصية"},
            {"title": "أدوات مجانية تزيد إنتاجيتك للضعف", "angle": "نصيحة عملية مباشرة"}
        ]

def analyze_trend(keyword):
    """
    Analyzes a specific keyword/trend and returns a JSON summary of the trend 
    along with two unique angles to write about it.
    """
    prompt = f"""
    You are an expert LinkedIn trend analyzer.
    The user wants to write about the topic/keyword: "{keyword}".
    What is the current conversation or trend around this topic? 
    Give me a brief summary of what people are saying, and 2 unique, non-cliché angles the user can take to stand out.
    
    IMPORTANT: Return ONLY valid JSON in the following format:
    {{
        "summary": "Brief summary in Arabic of the current trend/conversation",
        "angles": [
            "Angle 1 (Arabic)",
            "Angle 2 (Arabic)"
        ]
    }}
    Do not include markdown formatting like ```json or any other text.
    """
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print(f"[!] Error analyzing trend: {e}")
        return {
            "summary": "الذكاء الاصطناعي لم يتمكن من تحليل التريند حالياً.",
            "angles": ["حاول طرح سؤال للنقاش", "شارك تجربتك الشخصية السريعة"]
        }

def generate_smart_replies(post_text, context="engagement"):
    """
    Generates 3 unique, high-quality smart replies for a given LinkedIn post.
    context: 'engagement' (proactive comment on influencer's post) or 'reply' (reply to a comment on your post)
    Returns a JSON list of reply objects.
    """
    if context == "reply":
        instruction = "The user received this comment on their LinkedIn post and wants to reply professionally and warmly."
        types = ["شكر وترحيب بأسلوب شخصي", "رد يضيف معلومة إضافية مفيدة", "رد يطرح سؤالاً ليكمل الحوار"]
    else:
        instruction = "The user wants to leave a high-value comment on this LinkedIn post by an influencer to attract their followers."
        types = ["تعليق يضيف إحصائية أو معلومة نادرة", "تعليق يشارك تجربة شخصية مرتبطة", "تعليق يطرح سؤالاً ذكياً يثير نقاش"]

    prompt = f"""
    You are an expert LinkedIn engagement strategist.
    {instruction}
    
    Post/Comment text:
    ---
    {post_text}
    ---
    
    Write exactly 3 distinct, thoughtful replies in ARABIC. Each reply should be:
    - Natural, human-sounding, not generic or sycophantic
    - Max 3-4 sentences
    - Match these styles: {types[0]}, {types[1]}, {types[2]}
    
    IMPORTANT: Return ONLY valid JSON in the following format, no markdown:
    [
        {{"type": "{types[0]}", "text": "..."}},
        {{"type": "{types[1]}", "text": "..."}},
        {{"type": "{types[2]}", "text": "..."}}
    ]
    """
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print(f"[!] Error generating smart replies: {e}")
        return [
            {"type": "رد افتراضي", "text": "شكراً جزيلاً على هذا المحتوى القيّم، استمتعت بقراءته!"},
            {"type": "رد افتراضي", "text": "هذه النقطة مهمة جداً، وقد واجهت شيئاً مشابهاً في تجربتي."},
            {"type": "رد افتراضي", "text": "سؤال مثير للاهتمام، ما رأيك في...?"}
        ]
