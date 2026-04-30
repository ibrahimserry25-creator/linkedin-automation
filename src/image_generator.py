import os
import requests
from urllib.parse import quote

# We will use pollinations.ai for free image generation
# It generates an image based on the URL path.
IMAGE_API_URL = "https://image.pollinations.ai/prompt/{}"

def generate_image(prompt, filename):
    """
    Generates an image from a prompt and saves it locally.
    """
    print(f"Generating image for prompt: '{prompt}'...")
    import random
    import re
    # Clean the prompt: keep it under 200 characters to prevent URL too long errors
    clean_prompt = re.sub(r'[^a-zA-Z0-9\s,.-]', '', prompt)[:200]
    safe_prompt = quote(clean_prompt)
    
    # Add a custom seed to ensure the image is unique every time
    seed = random.randint(1, 999999)
    
    # Define "Servers" (Using Pollinations with different backend models as different servers)
    servers = [
        f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&enhance=true&seed={seed}&model=flux",  # Server 1
        f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&enhance=true&seed={seed}&model=turbo", # Server 2
        f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&enhance=true&seed={seed}"              # Server 3
    ]

    response = None
    try:
        # Try generating the AI prompt on multiple servers first
        for i, server_url in enumerate(servers):
            print(f"[*] Trying Server {i+1}...")
            try:
                response = requests.get(server_url, timeout=30)
                if response.status_code == 200:
                    print(f"[*] Server {i+1} succeeded!")
                    break
            except requests.exceptions.RequestException:
                print(f"[!] Server {i+1} timeout or connection error.")
                continue

        # If all servers failed with the AI prompt, try the safe background
        if not response or response.status_code != 200:
            print("[!] All AI prompt servers failed. Trying safe background fallback...")
            safe_fallback = "professional abstract minimalist business background, high quality"
            fallback_url = f"https://image.pollinations.ai/prompt/{quote(safe_fallback)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
            try:
                response = requests.get(fallback_url, timeout=30)
            except:
                pass
            
        # Ultimate fail-proof fallback (Picsum Photos - 99.99% uptime)
        if not response or response.status_code != 200:
            print("[!] Fallback failed. Using ultimate fail-proof fallback (Picsum)...")
            ultimate_fallback_url = f"https://picsum.photos/seed/{seed}/1024/1024"
            response = requests.get(ultimate_fallback_url, timeout=15)

        if response and response.status_code == 200:
            outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            
            filepath = os.path.join(outputs_dir, f"{filename}.jpg")
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"[*] Image saved to: {filepath}")
            return filepath
        else:
            print(f"[!] ALL image generation methods failed.")
            return None
    except Exception as e:
        print(f"[!] Error downloading image: {e}")
        return None
