#!/usr/bin/env python3

import os
import json
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from strava_client import StravaClient

def load_config() -> Dict[str, Any]:
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError("config.json not found. Please run download_strava_data.py first.")

def check_rate_limit_status(access_token: str) -> bool:
    """Check if we can make API requests or need to wait for rate limit reset"""
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
        
        if response.status_code == 200:
            return True
        elif response.status_code == 429:
            print("Rate limit exceeded. Checking reset time...")
            
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
                
            print(f"Waiting {wait_minutes} minutes for rate limit reset (until :{next_reset:02d})...")
            time.sleep(wait_minutes * 60 + 10)  # Add 10 seconds buffer
            
            # Check again
            return check_rate_limit_status(access_token)
        else:
            print(f"Unexpected API response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error checking rate limit: {e}")
        return False

def download_yearly_gps_data(client: StravaClient) -> Dict[int, Any]:
    """Download GPS data from the last year"""
    
    # Calculate date range (last 365 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"Downloading activities from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    all_activities = []
    page = 1
    
    while True:
        print(f"Fetching activities page {page}...")
        
        # Convert to Unix timestamps
        after = int(start_date.timestamp())
        before = int(end_date.timestamp())
        
        try:
            activities = client._make_request("athlete/activities", {
                'per_page': 200,
                'page': page,
                'after': after,
                'before': before
            })
            
            if not activities:
                break
            
            all_activities.extend(activities)
            print(f"  Found {len(activities)} activities on page {page}")
            page += 1
            
            # Safety check to prevent infinite loops
            if page > 50:  # Max ~10,000 activities
                print("Reached maximum page limit (50). Stopping.")
                break
                
        except Exception as e:
            print(f"Error fetching activities page {page}: {e}")
            break
    
    print(f"Total activities found: {len(all_activities)}")
    
    # Download GPS data for activities
    gps_data = {}
    gps_activity_count = 0
    
    for i, activity in enumerate(all_activities):
        activity_id = activity['id']
        activity_name = activity['name']
        activity_type = activity.get('type', 'Unknown')
        activity_date = activity.get('start_date', 'Unknown')
        
        print(f"[{i+1}/{len(all_activities)}] {activity_name} ({activity_type}) - {activity_date}")
        
        # Skip non-GPS activities
        if activity_type in ['WeightTraining', 'Yoga', 'Workout', 'Crossfit']:
            print("  → Skipping (no GPS expected)")
            continue
        
        try:
            gps_points = client.download_activity_gps_data(activity_id)
            
            if gps_points:
                gps_data[activity_id] = gps_points
                gps_activity_count += 1
                print(f"  → Downloaded {len(gps_points)} GPS points")
            else:
                print("  → No GPS data available")
                
        except Exception as e:
            print(f"  → Error downloading GPS data: {e}")
            continue
        
        # Progress update every 10 activities
        if (i + 1) % 10 == 0:
            print(f"Progress: {i+1}/{len(all_activities)} activities processed, {gps_activity_count} with GPS data")
            print(f"Rate limit usage: {client.rate_limiter.short_term_requests}/100")
    
    return gps_data

def main():
    print("Strava Yearly GPS Data Downloader")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    
    # Create output directory
    output_dir = config["data"]["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # Check rate limit before starting
    print("Checking API rate limit status...")
    if not check_rate_limit_status(config["strava"]["access_token"]):
        print("Cannot proceed due to rate limit issues. Please try again later.")
        return
    
    # Create Strava client
    client = StravaClient(
        client_id=config["strava"]["client_id"],
        client_secret=config["strava"]["client_secret"],
        access_token=config["strava"]["access_token"],
        refresh_token=config["strava"]["refresh_token"],
        config_file="config.json"
    )
    
    # Test authentication
    try:
        athlete = client.get_athlete()
        print(f"Authenticated as: {athlete['firstname']} {athlete['lastname']}")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return
    
    # Download yearly GPS data
    print("\nDownloading GPS data from the last year...")
    try:
        gps_data = download_yearly_gps_data(client)
        
        if not gps_data:
            print("No GPS data found in the last year.")
            return
        
        # Create timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save GPS data to file
        gps_filename = f"gps_data_yearly_{timestamp}.json"
        gps_data_file = os.path.join(output_dir, gps_filename)
        
        with open(gps_data_file, 'w') as f:
            json.dump(gps_data, f, indent=2)
        
        print(f"GPS data saved to: {gps_data_file}")
        
        # Save athlete info
        athlete_filename = f"athlete_info_yearly_{timestamp}.json"
        athlete_file = os.path.join(output_dir, athlete_filename)
        with open(athlete_file, 'w') as f:
            json.dump(athlete, f, indent=2)
        
        print(f"Athlete info saved to: {athlete_file}")
        
        # Update latest versions
        latest_gps_file = os.path.join(output_dir, "gps_data_latest.json")
        latest_athlete_file = os.path.join(output_dir, "athlete_info_latest.json")
        
        with open(latest_gps_file, 'w') as f:
            json.dump(gps_data, f, indent=2)
        with open(latest_athlete_file, 'w') as f:
            json.dump(athlete, f, indent=2)
            
        print(f"Latest versions updated: gps_data_latest.json, athlete_info_latest.json")
        
        # Show summary
        total_points = sum(len(points) for points in gps_data.values())
        print(f"\n📊 Yearly Download Summary:")
        print(f"  Activities with GPS: {len(gps_data)}")
        print(f"  Total GPS points: {total_points:,}")
        print(f"  Rate limit usage: {client.rate_limiter.short_term_requests}/100")
        print(f"  Daily usage: {client.rate_limiter.daily_requests}/1000")
        
        # Calculate file size
        file_size = os.path.getsize(gps_data_file)
        print(f"  GPS data file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
    except Exception as e:
        print(f"Failed to download yearly GPS data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\nYearly data download complete!")
    print(f"Files saved in: {output_dir}")

if __name__ == "__main__":
    main()