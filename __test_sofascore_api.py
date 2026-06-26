"""Test SofaScore mobile API for live incidents."""
import requests

# Mimic a SofaScore mobile app request
HEADERS = {
    "User-Agent": "SofaScore/23.0.0 (Android 14; Build/UP1A)",
    "Accept": "application/json",
    "Accept-Language": "en-US",
}

# We need an Event ID. Let's try to search first, 
# but if that's hard, we can try to list live matches.
# URL to list live football events
url = "https://api.sofascore.com/api/v1/sport/football/events/live"

try:
    r = requests.get(url, headers=HEADERS, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        events = data.get("events", [])
        print(f"Found {len(events)} live matches.")
        if events:
            # Pick the first match to test
            eid = events[0].get("id")
            print(f"Testing incidents for match ID: {eid}")
            incidents_url = f"https://api.sofascore.com/api/v1/event/{eid}/incidents"
            r2 = requests.get(incidents_url, headers=HEADERS, timeout=10)
            print(f"Incidents Status: {r2.status_code}")
            if r2.status_code == 200:
                incidents = r2.json().get("incidents", [])
                print(f"Found {len(incidents)} incidents.")
                for i in incidents[:3]:
                    print(f"  {i.get('type')}: {i.get('player', {}).get('name')}")
    else:
        print(f"Failed: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
