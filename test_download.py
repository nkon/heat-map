#!/usr/bin/env python3

import os
import json
from typing import Dict, Any
from strava_client import StravaClient

def test_download_sample():
    """Test downloading a small sample of GPS data"""
    
    print("Testing Sample GPS Data Download")
    print("=" * 35)
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Create output directory
    data_config = config["data"]
    output_dir = data_config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Authenticate with Strava
    strava_config = config["strava"]
    client = StravaClient(
        client_id=strava_config["client_id"],
        client_secret=strava_config["client_secret"],
        access_token=strava_config.get("access_token"),
        refresh_token=strava_config.get("refresh_token"),
        config_file="config.json"
    )
    
    try:
        # Test authentication
        athlete = client.get_athlete()
        print(f"✓ Authenticated as: {athlete['firstname']} {athlete['lastname']}")
        
        # Get first 5 activities only for testing
        print("Getting recent activities...")
        activities = client.get_activities(per_page=5, page=1)
        print(f"✓ Found {len(activities)} recent activities")
        
        if not activities:
            print("No activities found.")
            return
        
        # Download GPS data for these activities
        gps_data = {}
        
        for i, activity in enumerate(activities):
            activity_id = activity['id']
            activity_name = activity['name']
            activity_type = activity.get('type', 'Unknown')
            
            print(f"[{i+1}/{len(activities)}] {activity_name} ({activity_type})")
            
            # Skip non-GPS activities
            if activity_type in ['WeightTraining', 'Yoga', 'Workout']:
                print("  → Skipping (no GPS)")
                continue
            
            try:
                gps_points = client.download_activity_gps_data(activity_id)
                
                if gps_points:
                    gps_data[activity_id] = gps_points
                    print(f"  → Downloaded {len(gps_points)} GPS points")
                else:
                    print("  → No GPS data available")
                    
            except Exception as e:
                print(f"  → Error: {e}")
        
        print(f"\nTotal activities with GPS data: {len(gps_data)}")
        
        if gps_data:
            # Save GPS data to file
            gps_data_file = os.path.join(output_dir, data_config["gps_data_file"])
            with open(gps_data_file, 'w') as f:
                json.dump(gps_data, f, indent=2)
            
            print(f"✓ GPS data saved to: {gps_data_file}")
            
            # Save athlete info
            athlete_file = os.path.join(output_dir, "athlete_info.json")
            with open(athlete_file, 'w') as f:
                json.dump(athlete, f, indent=2)
            
            print(f"✓ Athlete info saved to: {athlete_file}")
            
            # Show file sizes
            gps_size = os.path.getsize(gps_data_file)
            athlete_size = os.path.getsize(athlete_file)
            print(f"✓ GPS data file size: {gps_size:,} bytes")
            print(f"✓ Athlete info file size: {athlete_size:,} bytes")
            
        else:
            print("✗ No GPS data was downloaded.")
            
        print(f"\nRate limit usage:")
        print(f"  Short term: {client.rate_limiter.short_term_requests}/100")
        print(f"  Daily: {client.rate_limiter.daily_requests}/1000")
            
    except Exception as e:
        print(f"✗ Download failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_download_sample()