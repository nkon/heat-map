#!/usr/bin/env python3

import json
from strava_client import StravaClient

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

strava_config = config['strava']

print("Creating StravaClient...")
client = StravaClient(
    client_id=strava_config['client_id'],
    client_secret=strava_config['client_secret'],
    access_token=strava_config.get('access_token'),
    refresh_token=strava_config.get('refresh_token'),
    config_file='config.json'
)

print("Getting athlete info...")
athlete = client.get_athlete()
print(f"Athlete: {athlete['firstname']} {athlete['lastname']}")

print("Getting first activity...")
activities = client.get_activities(per_page=1, page=1)
if activities:
    activity = activities[0]
    print(f"Activity: {activity['name']} ({activity['type']})")
    print("Trying to get GPS data...")
    gps_data = client.download_activity_gps_data(activity['id'])
    print(f"GPS points: {len(gps_data) if gps_data else 0}")
else:
    print("No activities found")

print("Test completed successfully!")