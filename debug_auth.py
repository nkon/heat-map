#!/usr/bin/env python3

import json
import requests
from strava_client import StravaClient

def debug_token_info():
    """Debug current token information and permissions"""
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    strava_config = config['strava']
    access_token = strava_config.get('access_token')
    
    print("Debugging Token Information")
    print("=" * 40)
    print(f"Access Token: {access_token[:20]}... (truncated)")
    print()
    
    # Test direct API calls to understand the issue
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Test 1: Get athlete info (should work)
    print("Test 1: Direct athlete API call")
    try:
        response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            athlete = response.json()
            print(f"✓ Athlete: {athlete['firstname']} {athlete['lastname']}")
            print(f"  ID: {athlete['id']}")
            print(f"  Country: {athlete.get('country', 'N/A')}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    print()
    
    # Test 2: Get activities (failing)
    print("Test 2: Direct activities API call")
    try:
        response = requests.get('https://www.strava.com/api/v3/athlete/activities?per_page=1', headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            activities = response.json()
            print(f"✓ Got {len(activities)} activities")
            if activities:
                print(f"  Latest: {activities[0]['name']}")
        else:
            print(f"✗ Error: {response.text}")
            print(f"  Headers: {response.headers}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    print()
    
    # Test 3: Check token with OAuth info endpoint
    print("Test 3: Token info from OAuth endpoint")
    try:
        # This endpoint doesn't exist in Strava API, but let's see what we get
        response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
        if response.status_code == 200:
            athlete = response.json()
            print("✓ Token is valid for athlete endpoint")
            
            # Check for specific fields that might indicate permissions
            if 'premium' in athlete:
                print(f"  Premium: {athlete['premium']}")
            if 'created_at' in athlete:
                print(f"  Account created: {athlete['created_at']}")
                
        print(f"  Response headers contain:")
        for header, value in response.headers.items():
            if 'rate' in header.lower() or 'limit' in header.lower():
                print(f"    {header}: {value}")
                
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    print()
    print("Recommendations:")
    print("1. The token works for athlete info but not for activities")
    print("2. This suggests a scope issue - the token may not have 'activity:read_all' scope")
    print("3. Run 'python get_refresh_token.py' to get a new token with correct scope")
    print("4. Make sure to authorize with 'activity:read_all' scope when prompted")

if __name__ == "__main__":
    debug_token_info()