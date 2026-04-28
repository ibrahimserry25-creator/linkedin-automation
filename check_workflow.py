import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN", "")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
REPO = "ibrahimserry25-creator/linkedin-automation"

for attempt in range(6):
    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=1", headers=headers)
    run = r.json()["workflow_runs"][0]
    status = run["status"]
    conclusion = run["conclusion"]
    print(f"Attempt {attempt+1}: Status={status}, Conclusion={conclusion}")
    
    if status == "completed":
        run_id = run["id"]
        r2 = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/jobs", headers=headers)
        job_id = r2.json()["jobs"][0]["id"]
        r3 = requests.get(f"https://api.github.com/repos/{REPO}/actions/jobs/{job_id}/logs", headers=headers)
        with open("github_logs.txt", "w", encoding="utf-8") as f:
            f.write(r3.text)
        print(f"Done! Result: {conclusion}")
        print("Logs saved to github_logs.txt")
        break
    
    print("Waiting 30s...")
    time.sleep(30)
