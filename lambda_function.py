import os
import json
import base64
import urllib.request
import urllib.parse
import urllib.error

def lambda_handler(event, context):
    print("[*] Waking up LinkedIn Smart Monitor...")
    
    # 1. Load Environment Variables
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_key:
        print("[!] Missing GEMINI_API_KEY!")
        return {"statusCode": 500, "body": "Missing ENV variables"}

    # 2. Extract Cookies (Hardcoded to bypass AWS 4KB Env Limit)
    li_at = "AQEDAVodx64DHp5XAAABndd9nXUAAAGd-4ohdU0ABY2RuFdlWjlgo3scWiKYIQ7Sy1-md6O3VJSAPNf0Ed7xvF3vdAxtB9PwGTeU_RzFfJV5CMKQFCLYFOAw_y-5DXitTNG1v2GWmIlxN_w4gGV-fJor"
    jsessionid = "ajax:1226479678417237517"
    csrf_token = jsessionid
    cookie_header = f"li_at={li_at}; JSESSIONID={jsessionid}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/vnd.linkedin.normalized+json+2.1",
        "csrf-token": csrf_token,
        "Cookie": cookie_header,
        "x-li-lang": "ar_AE"
    }

    # Helper function for HTTP requests
    def make_request(url, method="GET", payload=None):
        req = urllib.request.Request(url, headers=headers, method=method)
        if payload:
            req.add_header("Content-Type", "application/json")
            data = json.dumps(payload).encode("utf-8")
        else:
            data = None
            
        try:
            with urllib.request.urlopen(req, data=data, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"[!] HTTP Error {e.code} on {url}")
            return None
        except Exception as e:
            print(f"[!] Request Error on {url}: {e}")
            return None

    # 3. Get My Profile URN
    me_data = make_request("https://www.linkedin.com/voyager/api/me")
    if not me_data or "miniProfile" not in me_data:
        print("[!] Failed to get profile URN. Cookies might be expired.")
        return {"statusCode": 401, "body": "Auth failed"}
    
    my_urn = me_data["miniProfile"]["entityUrn"]
    my_profile_id = my_urn.split(":")[-1]
    print(f"[*] Authenticated as Profile ID: {my_profile_id}")

    # 4. Get Recent Posts
    posts_url = f"https://www.linkedin.com/voyager/api/identity/profileUpdatesV2?count=3&includeLongTermHistory=true&profileUrn={urllib.parse.quote(my_urn)}&q=memberShareFeed"
    posts_data = make_request(posts_url)
    
    if not posts_data or "elements" not in posts_data:
        print("[!] Failed to fetch posts.")
        return {"statusCode": 500, "body": "Failed to fetch posts"}

    replied_count = 0

    # 5. Check Comments on Each Post
    for post in posts_data["elements"]:
        post_urn = post.get("urn")
        if not post_urn: continue
        
        comments_url = f"https://www.linkedin.com/voyager/api/feed/updates/{urllib.parse.quote(post_urn)}/comments?count=20&q=comments"
        comments_data = make_request(comments_url)
        
        if not comments_data or "elements" not in comments_data:
            continue
            
        for comment in comments_data["elements"]:
            commenter_urn = comment.get("commenter", {}).get("urn")
            
            # Skip my own comments
            if commenter_urn == my_urn:
                continue
                
            comment_text = ""
            try:
                comment_text = comment["comment"]["values"][0]["value"]
            except:
                pass
            
            if not comment_text: continue
            
            # Check if I already replied
            comments_urn = comment.get("urn")
            replies_url = f"https://www.linkedin.com/voyager/api/feed/updates/{urllib.parse.quote(post_urn)}/comments?count=10&q=comments&threadUrn={urllib.parse.quote(comments_urn)}"
            replies_data = make_request(replies_url)
            
            already_replied = False
            if replies_data and "elements" in replies_data:
                for rep in replies_data["elements"]:
                    if rep.get("commenter", {}).get("urn") == my_urn:
                        already_replied = True
                        break
                        
            if already_replied:
                continue
                
            print(f"[*] New comment found: '{comment_text}'")
            
            # 6. Generate AI Reply using Gemini REST API
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            prompt = f"أنت خبير على لينكدإن. أحدهم كتب لك هذا التعليق: '{comment_text}'. اكتب رداً قصيراً واحترافياً وودوداً باللغة العربية. الرد يجب أن يكون جملة واحدة أو اثنتين فقط ولا تضع أي هاشتاجات."
            
            ai_payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 100}
            }
            
            # Custom request to Gemini
            ai_req = urllib.request.Request(gemini_url, headers={"Content-Type": "application/json"}, method="POST")
            ai_data = json.dumps(ai_payload).encode("utf-8")
            ai_reply_text = "شكراً جزيلاً لمرورك وتعليقك الرائع! 😊" # Fallback
            
            try:
                with urllib.request.urlopen(ai_req, data=ai_data, timeout=10) as ai_res:
                    ai_json = json.loads(ai_res.read().decode("utf-8"))
                    ai_reply_text = ai_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                print(f"[!] Gemini AI Failed, using fallback. Error: {e}")
                
            print(f"[*] AI Generated Reply: '{ai_reply_text}'")
            
            # 7. Post the Reply to LinkedIn
            reply_payload = {
                "comment": {
                    "values": [{"value": ai_reply_text}]
                },
                "threadUrn": comments_urn
            }
            
            post_reply_url = f"https://www.linkedin.com/voyager/api/feed/updates/{urllib.parse.quote(post_urn)}/comments?action=create"
            reply_res = make_request(post_reply_url, method="POST", payload=reply_payload)
            
            if reply_res is not None:
                print("[+] Successfully replied to comment!")
                replied_count += 1
            else:
                print("[!] Failed to post reply to LinkedIn.")

    print(f"[*] Run complete. Replied to {replied_count} comments.")
    return {"statusCode": 200, "body": f"Replied to {replied_count} comments"}
