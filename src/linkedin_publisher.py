import os
import requests
from dotenv import load_dotenv
import sqlite3
from urllib.parse import quote

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "social_posts.db")

def publish_to_linkedin(post_id):
    """
    Publishes a post to LinkedIn with image support using the UGC API.
    """
    # 1. Fetch post from DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT topic, content, image_path FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return False, "المنشور غير موجود في قاعدة البيانات"
        
    topic, content, image_path = row
    
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return False, "لم يتم العثور على مفتاح الوصول للينكدإن."
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # 2. Fetch User URN
    try:
        userinfo_response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
        if userinfo_response.status_code != 200:
            return False, f"فشل في جلب بيانات المستخدم: {userinfo_response.text}"
        
        person_urn = f"urn:li:person:{userinfo_response.json().get('sub')}"
    except Exception as e:
        return False, f"خطأ أثناء الاتصال بلينكدإن لجلب البيانات: {e}"

    image_urn = None
    # 3. Handle Image Upload (Optional)
    if image_path and os.path.exists(image_path):
        try:
            # Step A: Register Upload
            register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": person_urn,
                    "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
                }
            }
            reg_res = requests.post(register_url, headers=headers, json=register_data)
            if reg_res.status_code == 200:
                upload_url = reg_res.json()['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
                image_urn = reg_res.json()['value']['asset']

                # Step B: Upload Binary
                with open(image_path, 'rb') as f:
                    binary_data = f.read()
                
                requests.put(upload_url, headers={"Authorization": f"Bearer {token}"}, data=binary_data)
        except Exception as e:
            print(f"Warning: Image upload process failed: {e}")

    # 4. Final Publish
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    media_category = "IMAGE" if image_urn else "NONE"
    
    post_data = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": media_category
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    if image_urn:
        post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
            "status": "READY",
            "description": {"text": topic},
            "media": image_urn,
            "title": {"text": topic}
        }]

    try:
        post_response = requests.post(post_url, headers=headers, json=post_data)
        if post_response.status_code == 201:
            urn = post_response.headers.get("x-restli-id", "")
            post_link = f"https://www.linkedin.com/feed/update/{urn}/" if urn else ""
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if post_link:
                cursor.execute("UPDATE posts SET status = 'Published', post_url = ? WHERE id = ?", (post_link, post_id))
            else:
                cursor.execute("UPDATE posts SET status = 'Published' WHERE id = ?", (post_id,))
            conn.commit()
            conn.close()
            return True, "تم النشر بنجاح مع الصورة! 🖼️✨"
        else:
            return False, f"فشل النشر: {post_response.text}"
    except Exception as e:
        return False, f"حدث خطأ أثناء محاولة النشر: {str(e)}"

def post_comment_on_linkedin(post_urn: str, comment_text: str) -> tuple[bool, str]:
    """
    Posts a comment reply on a LinkedIn post via the Social Actions API.
    post_urn: The URN of the post to comment on (e.g. urn:li:ugcPost:1234567890)
    """
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return False, "لم يتم العثور على مفتاح الوصول للينكدإن."

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # Get person URN first
    try:
        userinfo_response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
        if userinfo_response.status_code != 200:
            return False, f"فشل في جلب بيانات المستخدم: {userinfo_response.text}"
        person_urn = f"urn:li:person:{userinfo_response.json().get('sub')}"
    except Exception as e:
        return False, f"خطأ في الاتصال: {e}"

    # Post the comment via Social Actions API
    from urllib.parse import quote as url_quote
    comment_url = f"https://api.linkedin.com/v2/socialActions/{url_quote(post_urn, safe='')}/comments"
    comment_data = {
        "actor": person_urn,
        "message": {
            "text": comment_text
        }
    }

    try:
        res = requests.post(comment_url, headers=headers, json=comment_data)
        if res.status_code in [200, 201]:
            return True, "تم نشر التعليق بنجاح على لينكدإن! ✅"
        else:
            return False, f"فشل نشر التعليق: {res.text}"
    except Exception as e:
        return False, f"خطأ أثناء نشر التعليق: {e}"


def check_linkedin_token_health() -> tuple[bool, str]:
    """
    Checks if the LinkedIn access token is still valid.
    Returns (is_healthy: bool, message: str)
    """
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return False, "❌ لا يوجد LINKEDIN_ACCESS_TOKEN في ملف .env"

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    try:
        res = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=10)
        if res.status_code == 200:
            name = res.json().get("name", "Unknown")
            return True, f"✅ التوكن سليم - مسجل دخول كـ: {name}"
        elif res.status_code == 401:
            return False, "⚠️ انتهت صلاحية التوكن (401 Unauthorized). يجب تجديد LINKEDIN_ACCESS_TOKEN في ملف .env"
        else:
            return False, f"⚠️ استجابة غير متوقعة من لينكدإن: {res.status_code} - {res.text}"
    except Exception as e:
        return False, f"❌ خطأ في الاتصال بلينكدإن: {e}"


def delete_linkedin_post(post_id):
    """
    Deletes a post from LinkedIn if it was published.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT post_url FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return True, "لم يتم نشر المنشور على لينكدإن أو لا يوجد رابط له."
        
    post_url = row[0]
    import re
    match = re.search(r'(urn:li:[a-zA-Z]+:\d+)', post_url)
    if not match:
        return True, "لم يتم العثور على معرف لينكدإن صالح في الرابط."
        
    urn = match.group(1)
    
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return False, "لم يتم العثور على مفتاح الوصول للينكدإن."
        
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    if "ugcPost" in urn:
        endpoint = f"https://api.linkedin.com/v2/ugcPosts/{quote(urn)}"
    elif "share" in urn:
        endpoint = f"https://api.linkedin.com/v2/shares/{quote(urn)}"
    else:
        endpoint = f"https://api.linkedin.com/v2/ugcPosts/{quote(urn)}"
        
    try:
        res = requests.delete(endpoint, headers=headers)
        if res.status_code in [200, 202, 204]:
            return True, "تم الحذف بنجاح من لينكدإن."
        else:
            return False, f"فشل الحذف من لينكدإن: {res.text}"
    except Exception as e:
        return False, f"حدث خطأ أثناء الحذف: {str(e)}"
