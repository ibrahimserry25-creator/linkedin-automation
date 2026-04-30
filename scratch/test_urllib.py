import json
import urllib.request
import urllib.parse
import urllib.error

li_at = "AQEDAVodx64DHp5XAAABndd9nXUAAAGd-4ohdU0ABY2RuFdlWjlgo3scWiKYIQ7Sy1-md6O3VJSAPNf0Ed7xvF3vdAxtB9PwGTeU_RzFfJV5CMKQFCLYFOAw_y-5DXitTNG1v2GWmIlxN_w4gGV-fJor"
jsessionid = "ajax:1226479678417237517"
csrf_token = jsessionid
cookie_header = f'li_at={li_at}; JSESSIONID="{jsessionid}"'

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/vnd.linkedin.normalized+json+2.1",
    "csrf-token": csrf_token,
    "Cookie": cookie_header,
    "x-restli-protocol-version": "2.0.0"
}

req = urllib.request.Request("https://www.linkedin.com/voyager/api/me", headers=headers, method="GET")

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        print("Success:", response.status)
        print(response.read().decode("utf-8")[:100])
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print("Error:", e)
