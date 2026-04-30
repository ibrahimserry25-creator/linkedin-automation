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
    Tries Pexels for a real photo first. If it fails, falls back to Pollinations AI or Picsum.
    """
    print(f"[*] Generating/Fetching image for: '{prompt}'...")
    
    # 1. Try Pexels first for real stock photos!
    filepath = get_pexels_image(prompt, filename)
    if filepath:
        print(f"[+] Real stock photo saved to: {filepath}")
        return filepath
        
    print("[!] Pexels failed or no results. Falling back to AI Image Generation...")
    
    # 2. Fallback to Pollinations AI
    clean_prompt = re.sub(r'[^a-zA-Z0-9\s,.-]', '', prompt)[:200]
    safe_prompt = quote(clean_prompt)
    seed = random.randint(1, 999999)
    
    servers = [
        f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&enhance=true&seed={seed}&model=flux",
        f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&enhance=true&seed={seed}&model=turbo"
    ]

    for i, server_url in enumerate(servers):
        print(f"[*] Trying AI Server {i+1}...")
        try:
            response = requests.get(server_url, timeout=30)
            if response.status_code == 200:
                outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
                os.makedirs(outputs_dir, exist_ok=True)
                filepath = os.path.join(outputs_dir, f"{filename}.jpg")
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"[+] AI Image saved to: {filepath}")
                return filepath
        except:
            continue

    # 3. Ultimate Fallback to Picsum
    print("[!] All methods failed. Using ultimate Picsum fallback...")
    try:
        response = requests.get(f"https://picsum.photos/seed/{seed}/1024/1024", timeout=15)
        outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
        filepath = os.path.join(outputs_dir, f"{filename}.jpg")
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    except:
        return None
