#!/usr/bin/env python3

import json
import requests
import time
from datetime import datetime

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

access_token = config['strava']['access_token']
headers = {'Authorization': f'Bearer {access_token}'}

print("Checking Strava API Rate Limit Status")
print("=" * 40)

# Make a simple request to check headers
response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)

print(f"Response Status: {response.status_code}")
print(f"Timestamp: {datetime.now()}")
print()

# Check rate limit headers
rate_limit_headers = {}
for header, value in response.headers.items():
    if 'rate' in header.lower() or 'limit' in header.lower():
        rate_limit_headers[header] = value
        print(f"{header}: {value}")

print()

if response.status_code == 429:
    print("❌ Rate limit exceeded!")
    
    # Parse rate limit info
    if 'x-ratelimit-usage' in rate_limit_headers:
        usage = rate_limit_headers['x-ratelimit-usage']
        print(f"Usage: {usage}")
    
    if 'x-ratelimit-limit' in rate_limit_headers:
        limit = rate_limit_headers['x-ratelimit-limit']
        print(f"Limit: {limit}")
    
    print()
    print("Solutions:")
    print("1. Wait for rate limit to reset (typically 15 minutes)")
    print("2. Check if you have been making too many requests")
    print("3. Strava limits: 100 requests per 15 minutes, 1000 per day")
    
    # Calculate wait time (rough estimate)
    current_minute = datetime.now().minute
    next_quarter = ((current_minute // 15) + 1) * 15
    if next_quarter >= 60:
        next_quarter = 0
    
    minutes_to_wait = (next_quarter - current_minute) % 15
    if minutes_to_wait == 0:
        minutes_to_wait = 15
    
    print(f"4. Estimated wait time: {minutes_to_wait} minutes")
    
elif response.status_code == 200:
    print("✅ API is accessible!")
    athlete = response.json()
    print(f"Authenticated as: {athlete['firstname']} {athlete['lastname']}")
    
else:
    print(f"❓ Unexpected status: {response.status_code}")
    print(f"Response: {response.text}")

print(f"\nCurrent time: {datetime.now()}")
print("Rate limits typically reset every 15 minutes at :00, :15, :30, :45")