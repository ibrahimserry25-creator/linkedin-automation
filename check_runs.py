import requests
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

r = requests.get(
    'https://api.github.com/repos/ibrahimserry25-creator/linkedin-automation/actions/runs?per_page=40',
    headers={
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
)
data = r.json()
runs = data.get('workflow_runs', [])

print(f"Total runs found: {len(runs)}")
print("-" * 90)
print(f"{'#':>4} | {'Event':18s} | {'Created At (UTC)':25s} | {'Status':10s} | {'Conclusion'}")
print("-" * 90)

for run in runs:
    print(f"{run['run_number']:4d} | {run['event']:18s} | {run['created_at']:25s} | {run['status']:10s} | {run.get('conclusion', 'N/A')}")
