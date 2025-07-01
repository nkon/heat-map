#!/usr/bin/env python3

import os
import json
import time
import requests
from typing import Dict, Any
from datetime import datetime
from strava_client import StravaClient


def load_config() -> Dict[str, Any]:
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Create default config file
    default_config = {
        "strava": {
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "access_token": "YOUR_ACCESS_TOKEN"
        },
        "data": {
            "output_dir": "strava_data",
            "gps_data_file": "gps_data.json"
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Created {config_file}. Please update it with your Strava API credentials.")
    return default_config


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

def authenticate_strava(config: Dict[str, Any]) -> StravaClient:
    strava_config = config["strava"]
    
    client = StravaClient(
        client_id=strava_config["client_id"],
        client_secret=strava_config["client_secret"],
        access_token=strava_config.get("access_token"),
        refresh_token=strava_config.get("refresh_token"),
        config_file="config.json"
    )
    
    # If no access token, help user authenticate
    if not client.access_token or client.access_token == "YOUR_ACCESS_TOKEN":
        print("Strava authentication required.")
        print("Please visit the following URL to authorize the application:")
        print(client.get_authorization_url("http://localhost:8000/callback"))
        print()
        auth_code = input("Enter the authorization code from the callback URL: ").strip()
        
        token_data = client.exchange_code_for_token(auth_code)
        
        # Update config with new token
        config["strava"]["access_token"] = token_data["access_token"]
        config["strava"]["refresh_token"] = token_data["refresh_token"]
        
        with open("config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print("Authentication successful! Token saved to config.json")
    
    return client


def main():
    print("Strava GPS Data Downloader")
    print("=" * 30)
    
    # Load configuration
    config = load_config()
    
    # Create output directory
    data_config = config["data"]
    output_dir = data_config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # Check rate limit before starting
    print("Checking API rate limit status...")
    if not check_rate_limit_status(config["strava"]["access_token"]):
        print("Cannot proceed due to rate limit issues. Please try again later.")
        return
    
    # Authenticate with Strava
    try:
        client = authenticate_strava(config)
        
        # Test authentication
        athlete = client.get_athlete()
        print(f"Authenticated as: {athlete['firstname']} {athlete['lastname']}")
        
    except Exception as e:
        print(f"Authentication failed: {e}")
        return
    
    # Download GPS data
    print("\nDownloading GPS data from Strava...")
    try:
        gps_data = client.download_all_gps_data()
        print(f"Downloaded GPS data from {len(gps_data)} activities")
        
        if not gps_data:
            print("No GPS data found. Make sure you have activities with GPS tracks.")
            return
        
        # Create timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save GPS data to file with descriptive name
        base_filename = data_config["gps_data_file"].replace('.json', '')
        gps_filename = f"{base_filename}_{timestamp}.json"
        gps_data_file = os.path.join(output_dir, gps_filename)
        
        with open(gps_data_file, 'w') as f:
            json.dump(gps_data, f, indent=2)
        
        print(f"GPS data saved to: {gps_data_file}")
        
        # Save athlete info with timestamp
        athlete_filename = f"athlete_info_{timestamp}.json"
        athlete_file = os.path.join(output_dir, athlete_filename)
        with open(athlete_file, 'w') as f:
            json.dump(athlete, f, indent=2)
        
        print(f"Athlete info saved to: {athlete_file}")
        
        # Also save a 'latest' version for easy access by other scripts
        latest_gps_file = os.path.join(output_dir, "gps_data_latest.json")
        latest_athlete_file = os.path.join(output_dir, "athlete_info_latest.json")
        
        with open(latest_gps_file, 'w') as f:
            json.dump(gps_data, f, indent=2)
        with open(latest_athlete_file, 'w') as f:
            json.dump(athlete, f, indent=2)
            
        print(f"Latest versions also saved as: gps_data_latest.json, athlete_info_latest.json")
        
        # Show summary
        total_points = sum(len(points) for points in gps_data.values())
        print(f"\n📊 Download Summary:")
        print(f"  Activities with GPS: {len(gps_data)}")
        print(f"  Total GPS points: {total_points:,}")
        print(f"  Rate limit usage: {client.rate_limiter.short_term_requests}/100")
            
    except Exception as e:
        print(f"Failed to download GPS data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\nData download complete!")
    print(f"Files saved in: {output_dir}")


if __name__ == "__main__":
    main()