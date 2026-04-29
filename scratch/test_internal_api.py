import json
import os
import requests
from urllib.parse import quote

def test_api_comments():
    state_file = "src/linkedin_state.json"
    if not os.path.exists(state_file):
        print("Error: src/linkedin_state.json not found")
        return

    with open(state_file, "r") as f:
        state = json.load(f)

    # Extract cookies from playwright state format
    cookies_dict = {}
    jsessionid = ""
    for c in state.get("cookies", []):
        cookies_dict[c["name"]] = c["value"]
        if c["name"] == "JSESSIONID":
            jsessionid = c["value"].strip('"')

    # Example Post URN (user provided earlier)
    # urn:li:share:7455031316 -> urn:li:activity:7455031316
    post_urn = "urn:li:activity:7455031317286641664"
    
    # Voyager API URL for comments
    url = f"https://www.linkedin.com/voyager/api/social/actions/{post_urn}/comments?count=10"
    
    headers = {
        "accept": "application/vnd.linkedin.normalized+json+2.1",
        "accept-language": "en-US,en;q=0.9",
        "csrf-token": jsessionid,
        "x-li-lang": "en_US",
        "x-li-page-instance": "urn:li:page:d_flagship3_feed;...",
        "x-li-track": '{"clientProjectionContext":{"unattributedRequests":["/voyager/api/social/actions/"]}}',
        "x-restli-protocol-version": "2.0.0",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"[*] Requesting comments for {post_urn} via Internal API...")
    response = requests.get(url, headers=headers, cookies=cookies_dict)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Data preview:")
        # Voyager returns a complex JSON, let's look for comments
        elements = data.get("elements", [])
        for i, el in enumerate(elements):
            text = el.get("commentary", {}).get("text", {}).get("text", "No text")
            author = el.get("actor", {}).get("name", {}).get("text", "Unknown")
            print(f" {i+1}. {author}: {text}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_api_comments()
