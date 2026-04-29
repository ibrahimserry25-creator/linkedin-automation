import requests

# Replace with your actual values
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8000/callback"
CODE = "CODE_FROM_URL"  # Replace with the code from the callback URL

# Exchange authorization code for access token
token_url = "https://www.linkedin.com/oauth/v2/accessToken"
data = {
    "grant_type": "authorization_code",
    "code": CODE,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}

response = requests.post(token_url, data=data)
if response.status_code == 200:
    token_data = response.json()
    print(f"Access Token: {token_data['access_token']}")
    print(f"Expires in: {token_data['expires_in']} seconds")
else:
    print(f"Error: {response.text}")
