#!/usr/bin/env python3

import json
import requests

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

access_token = config['strava']['access_token']
headers = {'Authorization': f'Bearer {access_token}'}

print("Testing direct API calls without rate limiting...")

# Test athlete
print("1. Getting athlete info...")
response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    athlete = response.json()
    print(f"✓ Athlete: {athlete['firstname']} {athlete['lastname']}")
else:
    print(f"✗ Error: {response.text}")

# Test activities
print("\n2. Getting activities...")
response = requests.get('https://www.strava.com/api/v3/athlete/activities?per_page=2', headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    activities = response.json()
    print(f"✓ Got {len(activities)} activities")
    if activities:
        activity = activities[0]
        print(f"Latest: {activity['name']} (ID: {activity['id']})")
        
        # Test GPS data
        print(f"\n3. Getting GPS data for activity {activity['id']}...")
        gps_url = f"https://www.strava.com/api/v3/activities/{activity['id']}/streams/latlng"
        response = requests.get(gps_url, headers=headers, params={'key_by_type': 'true'})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            streams = response.json()
            if 'latlng' in streams and streams['latlng']['data']:
                gps_points = streams['latlng']['data']
                print(f"✓ Got {len(gps_points)} GPS points")
                print(f"First point: {gps_points[0]}")
                print(f"Last point: {gps_points[-1]}")
            else:
                print("✗ No GPS data in response")
        else:
            print(f"✗ Error: {response.text}")
else:
    print(f"✗ Error: {response.text}")

print("\nDirect API test completed!")