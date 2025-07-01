#!/usr/bin/env python3

import json
from strava_client import StravaClient

def get_new_token_with_correct_scope():
    """Get a new token with the correct activity:read_all scope"""
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    strava_config = config['strava']
    
    print("Getting New Token with Correct Scope")
    print("=" * 40)
    print()
    
    # Create client
    client = StravaClient(
        client_id=strava_config['client_id'],
        client_secret=strava_config['client_secret']
    )
    
    # Get authorization URL with correct scope
    auth_url = client.get_authorization_url(
        redirect_uri="http://localhost:8000/callback",
        scope="activity:read_all"
    )
    
    print("Current token issue: Missing 'activity:read_permission' scope")
    print("Solution: Get new token with 'activity:read_all' scope")
    print()
    print("Steps to fix:")
    print("1. Visit this URL to re-authorize with correct scope:")
    print(f"   {auth_url}")
    print()
    print("2. Make sure to grant permission for 'View data about your activities'")
    print()
    print("3. After authorization, you'll be redirected to:")
    print("   http://localhost:8000/callback?state=&code=AUTHORIZATION_CODE&scope=read,activity:read_all")
    print()
    print("4. Copy the 'code' parameter from the URL")
    print()
    
    # Ask user if they want to proceed
    proceed = input("Ready to enter the authorization code? (y/n): ").strip().lower()
    
    if proceed != 'y':
        print("Please visit the URL above and get the authorization code first.")
        return
    
    # Get authorization code from user
    auth_code = input("Enter the authorization code: ").strip()
    
    if not auth_code:
        print("No authorization code provided. Exiting.")
        return
    
    try:
        # Exchange code for tokens
        print("Exchanging authorization code for tokens...")
        token_data = client.exchange_code_for_token(auth_code)
        
        print("✓ Successfully obtained new tokens!")
        print(f"Access Token: {token_data['access_token'][:20]}...")
        print(f"Refresh Token: {token_data['refresh_token'][:20]}...")
        print(f"Scope: {token_data.get('scope', 'Not specified')}")
        print(f"Expires At: {token_data['expires_at']}")
        print()
        
        # Update config file
        config['strava']['access_token'] = token_data['access_token']
        config['strava']['refresh_token'] = token_data['refresh_token']
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✓ Config file updated with new tokens!")
        print()
        
        # Test the new tokens immediately
        print("Testing new tokens...")
        athlete = client.get_athlete()
        print(f"✓ Authenticated as: {athlete['firstname']} {athlete['lastname']}")
        
        # Test activities access (this should work now)
        activities = client.get_activities(per_page=3, page=1)
        print(f"✓ Successfully retrieved {len(activities)} activities!")
        
        if activities:
            print("Recent activities:")
            for activity in activities:
                activity_type = activity.get('type', 'Unknown')
                start_date = activity.get('start_date', 'Unknown date')
                print(f"  - {activity['name']} ({activity_type}) - {start_date}")
        
        print()
        print("🎉 Success! You can now use the full application.")
        print("Run 'python download_strava_data.py' to download your GPS data.")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    get_new_token_with_correct_scope()