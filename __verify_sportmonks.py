"""Verify SportMonks connectivity by fetching today's matches"""
import sys; sys.path.insert(0, 'src')
from sportmonks_api import get_today_matches

matches = get_today_matches()
print(f"Found {len(matches)} matches via SportMonks.")
for m in matches:
    print(f"Match: {m.get('home_team')} vs {m.get('away_team')} [{m.get('status')}]")
