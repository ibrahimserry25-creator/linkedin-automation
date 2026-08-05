import os
import requests
import random
import re
from urllib.parse import quote
from src.database import is_image_url_used

def get_pexels_image(query, filename):
    """Fetches a real stock photo from Pexels."""
    pexels_key = os.getenv("PEXELS_API_KEY")
    if not pexels_key:
        print("[!] No PEXELS_API_KEY found.")
        return None
        
    print(f"[*] Searching Pexels for: '{query}'...")
    
    # Clean query to 1 or 2 keywords for better stock photo results
    clean_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
    words = clean_query.split()
    if len(words) > 3:
        clean_query = " ".join(words[:2]) + " business" # fallback to generic business

    headers = {"Authorization": pexels_key}
    url = f"https://api.pexels.com/v1/search?query={quote(clean_query)}&per_page=15&orientation=square"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("photos"):
                # Filter out used photos
                unused_photos = [p for p in data["photos"] if not is_image_url_used(p["src"]["large2x"])]
                if not unused_photos:
                    print("[!] All fetched photos from Pexels have been used previously.")
                    return None
                    
                # Pick a random photo from the unused ones
                photo = random.choice(unused_photos)
                image_url = photo["src"]["large2x"]
                
                print(f"[*] Found unique Pexels image! Downloading...")
                img_data = requests.get(image_url, timeout=15).content
                
                outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
                os.makedirs(outputs_dir, exist_ok=True)
                filepath = os.path.join(outputs_dir, f"{filename}.jpg")
                
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                return filepath
    except Exception as e:
        print(f"[!] Pexels search failed: {e}")
        
    return None

def get_unsplash_image(query, filename):
    """Fetches a real stock photo from Unsplash."""
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not unsplash_key:
        print("[!] No UNSPLASH_ACCESS_KEY found.")
        return None
        
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
                # Filter out used photos
                unused_photos = [p for p in data["results"] if not is_image_url_used(p["urls"]["regular"])]
                if not unused_photos:
                    print("[!] All fetched photos from Unsplash have been used previously.")
                    return None
                    
                photo = random.choice(unused_photos)
                image_url = photo["urls"]["regular"]
                
                print(f"[*] Found unique Unsplash image! Downloading...")
                img_data = requests.get(image_url, timeout=15).content
                
                outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
                os.makedirs(outputs_dir, exist_ok=True)
                filepath = os.path.join(outputs_dir, f"{filename}.jpg")
                
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                return filepath
    except Exception as e:
        print(f"[!] Unsplash search failed: {e}")
        
    return None

def generate_image(prompt, filename):
    """
    Fetches a stock photo from Pexels or Unsplash (50/50). Returns (filepath, source_name).
    """
    print(f"[*] Getting stock photo for: '{prompt}'...")
    
    choices = []
    if os.getenv("PEXELS_API_KEY"):
        choices.append("Pexels")
    if os.getenv("UNSPLASH_ACCESS_KEY"):
        choices.append("Unsplash")
        
    source = random.choice(choices) if choices else "Pexels"
    
    image_path = None
    if source == "Unsplash":
        image_path = get_unsplash_image(prompt, filename)
        if not image_path:
            source = "Pexels" # Fallback
            image_path = get_pexels_image(prompt, filename)
    else:
        image_path = get_pexels_image(prompt, filename)
        if not image_path and "Unsplash" in choices:
            source = "Unsplash" # Fallback
            image_path = get_unsplash_image(prompt, filename)
            
    if image_path:
        return image_path, source
        
    # Ultimate Fallback to Picsum
    print("[!] Pexels/Unsplash failed or keys missing. Using ultimate Picsum fallback...")
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

