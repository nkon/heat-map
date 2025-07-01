#!/usr/bin/env python3

import json
from strava_client import StravaClient

def test_authentication():
    """Test Strava authentication and token refresh functionality"""
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    strava_config = config['strava']
    
    print("Testing Strava Authentication")
    print("=" * 40)
    
    # Create client
    client = StravaClient(
        client_id=strava_config['client_id'],
        client_secret=strava_config['client_secret'],
        access_token=strava_config.get('access_token'),
        refresh_token=strava_config.get('refresh_token'),
        config_file='config.json'
    )
    
    print(f"Client ID: {client.client_id}")
    print(f"Has Access Token: {bool(client.access_token)}")
    print(f"Has Refresh Token: {bool(client.refresh_token)}")
    print()
    
    # Test if we need to authenticate
    if not client.access_token or client.access_token == "YOUR_ACCESS_TOKEN":
        print("No valid access token found.")
        print("You need to complete the OAuth flow:")
        print("1. Visit the following URL:")
        print(client.get_authorization_url("http://localhost:8000/callback"))
        print("2. After authorization, you'll be redirected to a URL with a 'code' parameter")
        print("3. Extract the code and use it to get tokens")
        return
    
    # Test API call
    try:
        print("Testing API call to get athlete info...")
        athlete = client.get_athlete()
        print(f"✓ Successfully authenticated as: {athlete['firstname']} {athlete['lastname']}")
        
        # Test getting activities (just first page)
        print("Testing activities retrieval...")
        activities = client.get_activities(per_page=5, page=1)
        print(f"✓ Successfully retrieved {len(activities)} activities")
        
        if activities:
            print("Recent activities:")
            for activity in activities[:3]:
                print(f"  - {activity['name']} ({activity['type']}) - {activity['start_date']}")
        
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        
        if "401" in str(e) and client.refresh_token:
            print("Attempting to refresh access token...")
            try:
                token_data = client.refresh_token_method(client.refresh_token)
                print("✓ Token refreshed successfully!")
                print("Testing API call again...")
                
                athlete = client.get_athlete()
                print(f"✓ Successfully authenticated as: {athlete['firstname']} {athlete['lastname']}")
                
            except Exception as refresh_error:
                print(f"✗ Token refresh failed: {refresh_error}")
                print("You may need to re-authenticate using the OAuth flow.")

if __name__ == "__main__":
    test_authentication()