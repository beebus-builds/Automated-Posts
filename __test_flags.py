"""Test flag fetching for Portugal vs Uzbekistan"""
import sys; sys.path.insert(0, 'src')
from card_generator import get_country_code, fetch_flag

team1 = "Portugal"
team2 = "Uzbekistan"

code1 = get_country_code(team1)
code2 = get_country_code(team2)

print(f"Team 1: {team1}, Code: {code1}")
print(f"Team 2: {team2}, Code: {code2}")

flag1 = fetch_flag(code1)
flag2 = fetch_flag(code2)

print(f"Flag 1 fetched: {flag1 is not None}")
print(f"Flag 2 fetched: {flag2 is not None}")
