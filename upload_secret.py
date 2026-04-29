import os
import base64
import json
import requests
from nacl import encoding, public
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO = "ibrahimserry25-creator/linkedin-automation"

def upload_github_secret(secret_name, secret_value):
    if not GITHUB_TOKEN:
        print(f"[Error] GITHUB_TOKEN is missing for {secret_name}")
        return False

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. Get repo public key
    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", headers=headers)
    if r.status_code != 200:
        print(f"[Error] getting public key ({r.status_code}): {r.text}")
        return False

    key_data = r.json()
    
    # 2. Encrypt the secret
    public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    # 3. Upload secret
    r = requests.put(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted_b64, "key_id": key_data["key_id"]}
    )
    
    if r.status_code in (201, 204):
        print(f"[Success] Secret {secret_name} updated successfully!")
        return True
    else:
        print(f"[Error] uploading {secret_name}: {r.text}")
        return False

if __name__ == "__main__":
    # Upload Gemini Key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        upload_github_secret("GEMINI_API_KEY", gemini_key)
    
    # Upload LinkedIn Token
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if linkedin_token:
        upload_github_secret("LINKEDIN_ACCESS_TOKEN", linkedin_token)
    
    # Upload LinkedIn Session State (Encoded)
    state_path = "src/linkedin_state.json"
    if os.path.exists(state_path):
        with open(state_path, "rb") as f:
            state_b64 = base64.b64encode(f.read()).decode()
            upload_github_secret("LINKEDIN_STATE_B64", state_b64)
