import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

models_to_test = [
    'gemini-1.5-pro',
    'gemini-pro',
    'gemini-flash-latest',
    'gemini-1.0-pro',
    'gemini-1.5-flash-latest'
]

for m in models_to_test:
    print(f"\nTesting {m}...")
    try:
        model = genai.GenerativeModel(m)
        response = model.generate_content("Hello")
        print(f"[SUCCESS] {m} works! Response: {response.text[:20]}")
    except Exception as e:
        print(f"[FAIL] {m}: {str(e)[:200]}")
