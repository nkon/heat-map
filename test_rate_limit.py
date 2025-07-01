#!/usr/bin/env python3

import json
from strava_client import StravaClient

def test_rate_limiting():
    """Test rate limiting functionality"""
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    strava_config = config['strava']
    
    print("Testing Rate Limiting")
    print("=" * 20)
    
    # Create client
    client = StravaClient(
        client_id=strava_config['client_id'],
        client_secret=strava_config['client_secret'],
        access_token=strava_config.get('access_token'),
        refresh_token=strava_config.get('refresh_token'),
        config_file='config.json'
    )
    
    print(f"Rate limiter status:")
    print(f"  Short term requests: {client.rate_limiter.short_term_requests}/100")
    print(f"  Daily requests: {client.rate_limiter.daily_requests}/1000")
    print(f"  Short term reset: {client.rate_limiter.short_term_reset}")
    print(f"  Daily reset: {client.rate_limiter.daily_reset}")
    print()
    
    try:
        # Test a few API calls
        print("Making API calls to test rate limiting...")
        
        # Get athlete info
        athlete = client.get_athlete()
        print(f"✓ Got athlete: {athlete['firstname']} {athlete['lastname']}")
        print(f"  Requests after call: {client.rate_limiter.short_term_requests}/100")
        
        # Get activities (small batch)
        activities = client.get_activities(per_page=10, page=1)
        print(f"✓ Got {len(activities)} activities")
        print(f"  Requests after call: {client.rate_limiter.short_term_requests}/100")
        
        if activities:
            # Get stream data for first activity (if it has GPS)
            first_activity = activities[0]
            print(f"Testing GPS data for activity: {first_activity['name']}")
            
            try:
                gps_data = client.download_activity_gps_data(first_activity['id'])
                if gps_data:
                    print(f"✓ Got GPS data with {len(gps_data)} points")
                else:
                    print("✓ Activity has no GPS data")
                print(f"  Requests after call: {client.rate_limiter.short_term_requests}/100")
            except Exception as e:
                print(f"✗ GPS data retrieval failed: {e}")
        
        print(f"\nFinal rate limiter status:")
        print(f"  Short term requests: {client.rate_limiter.short_term_requests}/100")
        print(f"  Daily requests: {client.rate_limiter.daily_requests}/1000")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")

if __name__ == "__main__":
    test_rate_limiting()