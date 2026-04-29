import os
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_linkedin_comments_via_api(post_urn: str) -> tuple[bool, list]:
    """
    Fetches comments from a LinkedIn post using LinkedIn API (socialActions).
    Returns (success, comments_list)
    Each comment is a dict with keys: author, text, author_urn, comment_urn
    """
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return False, []

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # LinkedIn API endpoint for comments
    from urllib.parse import quote as url_quote
    comments_url = f"https://api.linkedin.com/v2/socialActions/{url_quote(post_urn, safe='')}/comments"

    try:
        res = requests.get(comments_url, headers=headers)
        if res.status_code != 200:
            print(f"[!] LinkedIn API comments error: {res.status_code} - {res.text[:200]}")
            return False, []

        data = res.json()
        elements = data.get("elements", [])
        comments = []

        for elem in elements:
            # Extract comment text
            message = elem.get("message", {})
            text = message.get("text", "").strip()
            if not text:
                continue

            # Extract author info
            actor = elem.get("actor", "")
            author_name = "Unknown"
            if actor.startswith("urn:li:person:"):
                # Try to get author name from profile (optional)
                author_urn = actor
                # For simplicity, we'll just mark as "Unknown" since fetching profile requires extra API calls
                author_name = "Unknown"
            else:
                author_urn = actor
                author_name = actor

            comment_urn = elem.get("id", "")

            comments.append({
                "author": author_name,
                "text": text,
                "author_urn": author_urn,
                "comment_urn": comment_urn
            })

        return True, comments

    except Exception as e:
        print(f"[!] Exception fetching comments via API: {e}")
        return False, []

def test_api_comments():
    """Test function to verify API access"""
    # Test with a known post URN (you can replace with your actual post URN)
    test_urn = "urn:li:share:7454705480771309568"
    success, comments = fetch_linkedin_comments_via_api(test_urn)
    print(f"API Comments Test - Success: {success}, Comments: {len(comments)}")
    for c in comments[:3]:
        print(f"  - {c['author']}: {c['text'][:50]}...")

if __name__ == "__main__":
    test_api_comments()
