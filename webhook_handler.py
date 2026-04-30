import json
import os
import requests
from urllib.parse import quote

def lambda_handler(event, context):
    """
    AWS Lambda handler for LinkedIn webhooks
    Receives comment notifications and replies automatically
    """
    try:
        # Parse the webhook payload
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        print(f"[*] Received webhook: {json.dumps(body, indent=2)}")
        
        # Extract comment information
        comment_data = extract_comment_data(body)
        if not comment_data:
            print("[!] No actionable comment data found")
            return {"statusCode": 200, "body": "No action needed"}
            
        # Generate reply
        reply_text = generate_reply(comment_data['comment_text'])
        if not reply_text:
            print("[!] Failed to generate reply")
            return {"statusCode": 200, "body": "No reply generated"}
            
        # Post reply via LinkedIn API
        success, message = post_linkedin_reply(
            comment_data['post_urn'], 
            reply_text
        )
        
        if success:
            print(f"[✓] Reply posted successfully: {reply_text[:50]}...")
            return {"statusCode": 200, "body": "Reply posted successfully"}
        else:
            print(f"[!] Failed to post reply: {message}")
            return {"statusCode": 500, "body": f"Reply failed: {message}"}
            
    except Exception as e:
        print(f"[!] Lambda error: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

def extract_comment_data(webhook_body):
    """
    Extract relevant data from LinkedIn webhook payload
    """
    # LinkedIn webhook structure varies, try common patterns
    try:
        # Pattern 1: Social activity update
        if 'socialActivity' in webhook_body:
            activity = webhook_body['socialActivity']
            comment_text = activity.get('message', {}).get('text', '')
            post_urn = activity.get('parentUrn', '')
            author = activity.get('actor', '')
            
            if comment_text and post_urn:
                return {
                    'comment_text': comment_text,
                    'post_urn': post_urn,
                    'author': author
                }
        
        # Pattern 2: Comment notification
        if 'comment' in webhook_body:
            comment = webhook_body['comment']
            comment_text = comment.get('message', {}).get('text', '')
            post_urn = comment.get('object', '')
            author = comment.get('actor', '')
            
            if comment_text and post_urn:
                return {
                    'comment_text': comment_text,
                    'post_urn': post_urn,
                    'author': author
                }
                
    except Exception as e:
        print(f"[!] Error extracting comment data: {e}")
        
    return None

def generate_reply(comment_text):
    """
    Generate smart reply using Gemini API
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[!] GEMINI_API_KEY not found")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        اكتب رود ذكي ومختصر على هذا التعليق على LinkedIn:
        
        التعليق: "{comment_text}"
        
        الرد يجب أن يكون:
        - باللغة العربية
        - مهذب واحترافي
        - من 1-3 جمل
        - يفتح حوار
        
        الرد:
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"[!] Error generating reply: {e}")
        return None

def post_linkedin_reply(post_urn, reply_text):
    """
    Post reply using LinkedIn API
    """
    try:
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        if not token:
            return False, "LinkedIn access token not found"
            
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # Get person URN
        userinfo_response = requests.get(
            "https://api.linkedin.com/v2/userinfo", 
            headers=headers
        )
        if userinfo_response.status_code != 200:
            return False, f"Failed to get user info: {userinfo_response.text}"
            
        person_urn = f"urn:li:person:{userinfo_response.json().get('sub')}"
        
        # Post comment
        comment_url = f"https://api.linkedin.com/v2/socialActions/{quote(post_urn, safe='')}/comments"
        comment_data = {
            "actor": person_urn,
            "message": {"text": reply_text}
        }
        
        response = requests.post(comment_url, headers=headers, json=comment_data)
        if response.status_code in [200, 201]:
            return True, "Reply posted successfully"
        else:
            return False, f"API error: {response.text}"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"
