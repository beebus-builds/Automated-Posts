"""Delete ALL posts from the Facebook page"""
import os, requests
from dotenv import load_dotenv
load_dotenv()

SYSTEM_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")

r = requests.get("https://graph.facebook.com/v20.0/me/accounts", params={"access_token": SYSTEM_TOKEN}, timeout=10)
page_token = None
for acc in r.json().get("data", []):
    if acc.get("id") == PAGE_ID:
        page_token = acc.get("access_token")
        break

if not page_token:
    print("Failed to get page token")
    exit()

total = 0
after = None
while True:
    params = {"access_token": page_token, "limit": 100, "fields": "id"}
    if after:
        params["after"] = after
    r2 = requests.get(f"https://graph.facebook.com/v20.0/{PAGE_ID}/feed", params=params, timeout=15)
    data = r2.json()
    posts = data.get("data", [])
    if not posts:
        break
    for p in posts:
        r3 = requests.delete(f"https://graph.facebook.com/v20.0/{p['id']}", params={"access_token": page_token}, timeout=10)
        if r3.status_code == 200:
            total += 1
        if total % 50 == 0:
            print(f"Deleted {total} so far...")
    paging = data.get("paging", {})
    cursors = paging.get("cursors", {})
    after = cursors.get("after")
    if not after:
        break

print(f"Total deleted: {total}")
