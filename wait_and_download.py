#!/usr/bin/env python3

import json
import requests
import time
from datetime import datetime, timedelta
import os
from strava_client import StravaClient

def wait_for_rate_limit_reset():
    """Wait for Strava rate limit to reset"""
    
    print("Checking rate limit status...")
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    headers = {'Authorization': f'Bearer {config["strava"]["access_token"]}'}
    
    while True:
        response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
        
        if response.status_code == 200:
            print("✅ Rate limit cleared! Ready to proceed.")
            return True
        elif response.status_code == 429:
            # Calculate wait time based on current time
            now = datetime.now()
            current_minute = now.minute
            
            # Rate limits reset at :00, :15, :30, :45
            reset_minutes = [0, 15, 30, 45]
            next_reset = None
            
            for reset_min in reset_minutes:
                if reset_min > current_minute:
                    next_reset = reset_min
                    break
            
            if next_reset is None:
                next_reset = 60  # Next hour
            
            wait_minutes = (next_reset - current_minute) % 60
            
            if wait_minutes == 0:
                wait_minutes = 1  # At least 1 minute
                
            print(f"⏳ Rate limit active. Waiting {wait_minutes} minutes until :{next_reset:02d}...")
            time.sleep(wait_minutes * 60 + 10)  # Add 10 seconds buffer
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            return False

def download_sample_data():
    """Download a small sample of data for testing"""
    
    print("\n" + "="*50)
    print("Starting Sample Data Download")
    print("="*50)
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Create output directory
    output_dir = config["data"]["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # Create client
    client = StravaClient(
        client_id=config["strava"]["client_id"],
        client_secret=config["strava"]["client_secret"],
        access_token=config["strava"]["access_token"],
        refresh_token=config["strava"]["refresh_token"],
        config_file="config.json"
    )
    
    try:
        # Get athlete info
        print("Getting athlete info...")
        athlete = client.get_athlete()
        print(f"✓ Authenticated as: {athlete['firstname']} {athlete['lastname']}")
        
        # Get limited activities for testing
        print("Getting recent activities (limit 3)...")
        activities = client.get_activities(per_page=3, page=1)
        print(f"✓ Found {len(activities)} activities")
        
        # Download GPS data for these activities
        gps_data = {}
        
        for i, activity in enumerate(activities):
            activity_id = activity['id']
            activity_name = activity['name']
            activity_type = activity.get('type', 'Unknown')
            
            print(f"\n[{i+1}/{len(activities)}] Processing: {activity_name}")
            print(f"  Type: {activity_type}")
            print(f"  ID: {activity_id}")
            
            # Skip non-GPS activities
            if activity_type in ['WeightTraining', 'Yoga', 'Workout']:
                print("  → Skipping (no GPS expected)")
                continue
            
            try:
                print("  → Downloading GPS data...")
                gps_points = client.download_activity_gps_data(activity_id)
                
                if gps_points:
                    gps_data[activity_id] = gps_points
                    print(f"  ✓ Downloaded {len(gps_points)} GPS points")
                else:
                    print("  → No GPS data available")
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
        
        # Save data if we got any
        if gps_data:
            # Create timestamped filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save GPS data with descriptive name
            base_filename = config["data"]["gps_data_file"].replace('.json', '')
            gps_filename = f"{base_filename}_{timestamp}.json"
            gps_file = os.path.join(output_dir, gps_filename)
            
            with open(gps_file, 'w') as f:
                json.dump(gps_data, f, indent=2)
            print(f"\n✓ GPS data saved to: {gps_file}")
            
            # Save athlete info with timestamp
            athlete_filename = f"athlete_info_{timestamp}.json"
            athlete_file = os.path.join(output_dir, athlete_filename)
            with open(athlete_file, 'w') as f:
                json.dump(athlete, f, indent=2)
            print(f"✓ Athlete info saved to: {athlete_file}")
            
            # Also save latest versions
            latest_gps_file = os.path.join(output_dir, "gps_data_latest.json")
            latest_athlete_file = os.path.join(output_dir, "athlete_info_latest.json")
            
            with open(latest_gps_file, 'w') as f:
                json.dump(gps_data, f, indent=2)
            with open(latest_athlete_file, 'w') as f:
                json.dump(athlete, f, indent=2)
                
            print(f"✓ Latest versions saved as: gps_data_latest.json, athlete_info_latest.json")
            
            # Show summary
            total_points = sum(len(points) for points in gps_data.values())
            print(f"\n📊 Summary:")
            print(f"  Activities with GPS: {len(gps_data)}")
            print(f"  Total GPS points: {total_points:,}")
            print(f"  Rate limit usage: {client.rate_limiter.short_term_requests}/100")
            
            return True
        else:
            print("\n❌ No GPS data was downloaded")
            return False
            
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Wait for rate limit reset
    if wait_for_rate_limit_reset():
        # Download sample data
        success = download_sample_data()
        if success:
            print(f"\n🎉 Sample download completed successfully!")
            print("Files are saved in the strava_data/ directory.")
        else:
            print(f"\n❌ Download failed. Check the error messages above.")
    else:
        print("❌ Could not clear rate limit. Please try again later.")