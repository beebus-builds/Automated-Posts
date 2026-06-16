import os, requests
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
post_id = "1222303417625710_122098815213363971"
r = requests.delete(f"https://graph.facebook.com/v20.0/{post_id}?access_token={TOKEN}")
print("Delete response:", r.json())
