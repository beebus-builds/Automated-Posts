"""Check post count and delete in batches"""
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

# Get count
r2 = requests.get(f"https://graph.facebook.com/v20.0/{PAGE_ID}/feed", params={"access_token": page_token, "limit": 100, "fields": "id"}, timeout=15)
posts = r2.json().get("data", [])
print(f"Posts to delete: {len(posts)}")

# Delete in batches of 5 for speed
import time
deleted = 0
for p in posts:
    r3 = requests.delete(f"https://graph.facebook.com/v20.0/{p['id']}", params={"access_token": page_token}, timeout=10)
    if r3.status_code == 200:
        deleted += 1
        if deleted % 5 == 0:
            print(f"Deleted {deleted}")
    time.sleep(0.2)

print(f"Done: {deleted} deleted")
