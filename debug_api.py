import os, sys
sys.path.append(os.path.abspath("src"))
from football_api import get_standings, get_past_matches, get_upcoming_matches

# Set dummy key for testing if needed, though get_standings uses the configured one
os.environ["FOOTBALL_API_KEY"] = "0d8e8764bcad4be199bd73e88f71d680"

print("Testing Standings WC:")
print(get_standings("WC"))

print("\nTesting Past Matches WC (Length):", len(get_past_matches(days=3, comp_code="WC")))

print("\nTesting Upcoming Matches WC (Length):", len(get_upcoming_matches(days=3, comp_code="WC")))

