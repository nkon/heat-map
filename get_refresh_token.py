#!/usr/bin/env python3

import json
from strava_client import StravaClient

def get_refresh_token():
    """Get a refresh token through OAuth flow"""
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    strava_config = config['strava']
    
    print("Strava Refresh Token Setup")
    print("=" * 30)
    
    # Create client
    client = StravaClient(
        client_id=strava_config['client_id'],
        client_secret=strava_config['client_secret']
    )
    
    # Get authorization URL
    auth_url = client.get_authorization_url(
        redirect_uri="http://localhost:8000/callback",
        scope="activity:read_all"
    )
    
    print("Step 1: Visit the following URL to authorize the application:")
    print(auth_url)
    print()
    print("Step 2: After authorization, you'll be redirected to:")
    print("http://localhost:8000/callback?state=&code=AUTHORIZATION_CODE&scope=read,activity:read_all")
    print()
    
    # Get authorization code from user
    auth_code = input("Step 3: Enter the authorization code from the URL: ").strip()
    
    if not auth_code:
        print("No authorization code provided. Exiting.")
        return
    
    try:
        # Exchange code for tokens
        print("Exchanging authorization code for tokens...")
        token_data = client.exchange_code_for_token(auth_code)
        
        print("✓ Successfully obtained tokens!")
        print(f"Access Token: {token_data['access_token'][:20]}...")
        print(f"Refresh Token: {token_data['refresh_token'][:20]}...")
        print(f"Token Type: {token_data['token_type']}")
        print(f"Expires At: {token_data['expires_at']}")
        
        # Update config file
        config['strava']['access_token'] = token_data['access_token']
        config['strava']['refresh_token'] = token_data['refresh_token']
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✓ Config file updated with new tokens!")
        
        # Test the new tokens
        print("\nTesting new tokens...")
        athlete = client.get_athlete()
        print(f"✓ Authenticated as: {athlete['firstname']} {athlete['lastname']}")
        
        activities = client.get_activities(per_page=3, page=1)
        print(f"✓ Retrieved {len(activities)} activities")
        
        if activities:
            print("Recent activities:")
            for activity in activities:
                print(f"  - {activity['name']} ({activity['type']})")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    get_refresh_token()