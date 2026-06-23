"""Verify feed"""
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

r2 = requests.get(f"https://graph.facebook.com/v20.0/{PAGE_ID}/feed", params={"access_token": page_token, "limit": 10, "fields": "id,message,created_time"}, timeout=15)
posts = r2.json().get("data", [])
print(f"Posts: {len(posts)}")
for p in posts[:5]:
    msg = repr(p.get("message","")[:70])
    print(f"  {p.get('created_time','')[:19]} {msg}")
