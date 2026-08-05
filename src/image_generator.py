import os
import requests
import random
import re
from urllib.parse import quote
from src.database import is_image_url_used, get_kv, set_kv
from src.telegram_notifier import send_telegram_alert

def get_pexels_image(query, filename):
    """Fetches a real stock photo from Pexels. Returns (filepath, error_msg)."""
    pexels_key = os.getenv("PEXELS_API_KEY")
    if not pexels_key:
        return None, "No PEXELS_API_KEY found."
        
    print(f"[*] Searching Pexels for: '{query}'...")
    
    clean_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
    words = clean_query.split()
    if len(words) > 3:
        clean_query = " ".join(words[:2]) + " business" 

    headers = {"Authorization": pexels_key}
    url = f"https://api.pexels.com/v1/search?query={quote(clean_query)}&per_page=15&orientation=square"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("photos"):
                unused_photos = [p for p in data["photos"] if not is_image_url_used(p["src"]["large2x"])]
                if not unused_photos:
                    return None, "All fetched photos from Pexels have been used previously."
                    
                photo = random.choice(unused_photos)
                image_url = photo["src"]["large2x"]
                
                print(f"[*] Found unique Pexels image! Downloading...")
                img_data = requests.get(image_url, timeout=15).content
                
                outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
                os.makedirs(outputs_dir, exist_ok=True)
                filepath = os.path.join(outputs_dir, f"{filename}.jpg")
                
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                return filepath, None
            else:
                return None, "No photos found for this query on Pexels."
        else:
            return None, f"Pexels API Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Pexels Request Error: {str(e)}"
        
    return None, "Unknown Pexels error."

def get_unsplash_image(query, filename):
    """Fetches a real stock photo from Unsplash. Returns (filepath, error_msg)."""
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not unsplash_key:
        return None, "No UNSPLASH_ACCESS_KEY found."
        
    print(f"[*] Searching Unsplash for: '{query}'...")
    
    clean_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
    words = clean_query.split()
    if len(words) > 3:
        clean_query = " ".join(words[:2]) + " business"

    headers = {"Authorization": f"Client-ID {unsplash_key}"}
    url = f"https://api.unsplash.com/search/photos?query={quote(clean_query)}&per_page=15&orientation=squarish"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                unused_photos = [p for p in data["results"] if not is_image_url_used(p["urls"]["regular"])]
                if not unused_photos:
                    return None, "All fetched photos from Unsplash have been used previously."
                    
                photo = random.choice(unused_photos)
                image_url = photo["urls"]["regular"]
                
                print(f"[*] Found unique Unsplash image! Downloading...")
                img_data = requests.get(image_url, timeout=15).content
                
                outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
                os.makedirs(outputs_dir, exist_ok=True)
                filepath = os.path.join(outputs_dir, f"{filename}.jpg")
                
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                return filepath, None
            else:
                return None, "No photos found for this query on Unsplash."
        else:
            return None, f"Unsplash API Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Unsplash Request Error: {str(e)}"
        
    return None, "Unknown Unsplash error."

def generate_image(prompt, filename):
    """
    Strictly alternates between Pexels and Unsplash. Returns (filepath, source_name).
    Sends a Telegram alert if the primary choice fails.
    """
    print(f"[*] Getting stock photo for: '{prompt}'...")
    
    # Determine strict alternation
    last_source = get_kv("last_image_source") or "Unsplash"
    primary_source = "Pexels" if last_source == "Unsplash" else "Unsplash"
    
    # Save the new source choice
    set_kv("last_image_source", primary_source)
    
    image_path, error = None, None
    if primary_source == "Unsplash":
        image_path, error = get_unsplash_image(prompt, filename)
        if not image_path:
            send_telegram_alert(f"⚠️ <b>فشل سحب صورة من Unsplash</b>\nجاري اللجوء لـ Pexels كاحتياطي.\nالسبب: {error}")
            primary_source = "Pexels"
            image_path, error = get_pexels_image(prompt, filename)
    else:
        image_path, error = get_pexels_image(prompt, filename)
        if not image_path:
            send_telegram_alert(f"⚠️ <b>فشل سحب صورة من Pexels</b>\nجاري اللجوء لـ Unsplash كاحتياطي.\nالسبب: {error}")
            primary_source = "Unsplash"
            image_path, error = get_unsplash_image(prompt, filename)
            
    if image_path:
        return image_path, primary_source
        
    # Ultimate Fallback to Picsum
    print("[!] Pexels and Unsplash both failed. Using ultimate Picsum fallback...")
    seed = random.randint(1, 999999)
    try:
        response = requests.get(f"https://picsum.photos/seed/{seed}/1024/1024", timeout=15)
        outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        filepath = os.path.join(outputs_dir, f"{filename}.jpg")
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath, "Picsum"
    except:
        return None, "None"

