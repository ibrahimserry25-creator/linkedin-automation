"""Add LINKEDIN_STATE_B64 secret to GitHub repo"""
import os
import base64
import json
import requests
from nacl import encoding, public
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO = "ibrahimserry25-creator/linkedin-automation"

# Read and encode state file
with open("src/linkedin_state.json", "rb") as f:
    state_b64 = base64.b64encode(f.read()).decode()

# Get repo public key for encryption
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", headers=headers)
key_data = r.json()
print(f"Got public key: {key_data.get('key_id', 'ERROR')}")

# Encrypt the secret
public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
sealed_box = public.SealedBox(public_key)
encrypted = sealed_box.encrypt(state_b64.encode("utf-8"))
encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

# Upload secret
r = requests.put(
    f"https://api.github.com/repos/{REPO}/actions/secrets/LINKEDIN_STATE_B64",
    headers=headers,
    json={"encrypted_value": encrypted_b64, "key_id": key_data["key_id"]}
)
print(f"Secret upload status: {r.status_code}")
if r.status_code in (201, 204):
    print("✅ LINKEDIN_STATE_B64 secret added successfully!")
else:
    print(f"❌ Error: {r.text}")
