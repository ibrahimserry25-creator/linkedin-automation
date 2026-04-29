import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def list_models():
    if not API_KEY:
        print("Error: GEMINI_API_KEY is missing!")
        return

    print(f"[*] Listing models for API key: {API_KEY[:5]}...{API_KEY[-5:]}")
    
    # Try v1 API
    url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
    try:
        r = requests.get(url)
        print(f"Status (v1): {r.status_code}")
        if r.status_code == 200:
            models = r.json().get("models", [])
            print(f"Found {len(models)} models:")
            for m in models:
                print(f" - {m['name']} (Supported actions: {m['supportedGenerationMethods']})")
        else:
            print(f"Error v1: {r.text}")
    except Exception as e:
        print(f"Exception v1: {e}")

    print("-" * 30)
    
    # Try v1beta API
    url_beta = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        r = requests.get(url_beta)
        print(f"Status (v1beta): {r.status_code}")
        if r.status_code == 200:
            models = r.json().get("models", [])
            print(f"Found {len(models)} models (v1beta):")
            for m in models:
                print(f" - {m['name']}")
        else:
            print(f"Error v1beta: {r.text}")
    except Exception as e:
        print(f"Exception v1beta: {e}")

if __name__ == "__main__":
    list_models()
