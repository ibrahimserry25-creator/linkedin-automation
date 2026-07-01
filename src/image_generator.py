import os
import requests
import random
import re
from urllib.parse import quote

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
                # Pick a random photo from the top results to keep it diverse
                photo = random.choice(data["photos"])
                image_url = photo["src"]["large2x"]
                
                print(f"[*] Found Pexels image! Downloading...")
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

def generate_image(prompt, filename):
    """
    Fetches a real stock photo for the given prompt to ensure high quality without AI deformations.
    """
    print(f"[*] Getting stock photo for: '{prompt}'...")
    
    # 1. Try Pexels first for professional stock photos
    image_path = get_pexels_image(prompt, filename)
    if image_path:
        return image_path
        
    # 2. Ultimate Fallback to Picsum if Pexels fails or API key is missing
    print("[!] Pexels failed or key missing. Using ultimate Picsum fallback...")
    seed = random.randint(1, 999999)
    try:
        response = requests.get(f"https://picsum.photos/seed/{seed}/1024/1024", timeout=15)
        outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        filepath = os.path.join(outputs_dir, f"{filename}.jpg")
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    except:
        return None
