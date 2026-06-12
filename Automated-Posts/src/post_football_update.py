import requests
import os

# Configuration from environment variables
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')
FB_PAGE_ACCESS_TOKEN = os.environ.get('FB_PAGE_ACCESS_TOKEN')
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')

def get_football_data():
    # Example: Fetching upcoming matches (or whatever data you want)
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def post_to_facebook(message):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    print("Post successful!")

def main():
    data = get_football_data()
    # Simple formatting: just post the count of matches as an example
    # Replace this with real logic
    count = data.get('count', 0)
    message = f"Football Update: There are {count} matches scheduled!"
    post_to_facebook(message)

if __name__ == "__main__":
    main()
