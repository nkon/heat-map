#!/usr/bin/env python3

"""
Strava Authentication Utility

Centralizes authentication logic, OAuth flow handling, and client creation.
Eliminates duplication of authentication code across scripts.
"""

import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from strava_client import StravaClient
from strava_config import StravaConfig


class StravaAuthenticator:
    """Handles Strava authentication and client creation"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_manager = StravaConfig(config_file)
        self.config = self.config_manager.load()
    
    def create_client(self) -> StravaClient:
        """
        Create and authenticate Strava client
        
        Returns:
            Authenticated StravaClient instance
            
        Raises:
            ValueError: If credentials are not configured
            Exception: If authentication fails
        """
        if not self.config_manager.validate_strava_credentials():
            raise ValueError("Strava credentials not configured. Please update config.json")
        
        strava_config = self.config_manager.get_strava_config()
        
        client = StravaClient(
            client_id=strava_config["client_id"],
            client_secret=strava_config["client_secret"],
            access_token=strava_config.get("access_token"),
            refresh_token=strava_config.get("refresh_token"),
            config_file=self.config_manager.config_file
        )
        
        # Verify authentication
        try:
            athlete = client.get_athlete()
            print(f"✓ Authenticated as: {athlete['firstname']} {athlete['lastname']}")
            return client
        except Exception as e:
            raise Exception(f"Authentication failed: {e}")
    
    def check_rate_limit_status(self, access_token: str = None) -> Tuple[bool, int]:
        """
        Check current rate limit status
        
        Args:
            access_token: Access token to check (uses config if not provided)
            
        Returns:
            Tuple of (can_proceed, wait_seconds)
        """
        if not access_token:
            access_token = self.config_manager.get("strava.access_token")
            if not access_token or access_token == "YOUR_ACCESS_TOKEN":
                raise ValueError("No valid access token available")
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
            
            if response.status_code == 200:
                return True, 0
            elif response.status_code == 429:
                # Rate limit exceeded, calculate wait time
                wait_seconds = self._calculate_rate_limit_wait()
                return False, wait_seconds
            elif response.status_code == 401:
                raise Exception("Invalid or expired access token. Please refresh your tokens.")
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to check rate limit status: {e}")
    
    def _calculate_rate_limit_wait(self) -> int:
        """
        Calculate seconds to wait for rate limit reset
        
        Returns:
            Seconds to wait until next rate limit window
        """
        now = datetime.now()
        current_minute = now.minute
        
        # Strava resets rate limits at :00, :15, :30, :45
        reset_minutes = [0, 15, 30, 45]
        next_reset_minute = None
        
        for reset_minute in reset_minutes:
            if current_minute < reset_minute:
                next_reset_minute = reset_minute
                break
        
        if next_reset_minute is None:
            # Next reset is at the top of the next hour
            next_reset_minute = 0
            next_reset_hour = now.hour + 1
            if next_reset_hour >= 24:
                next_reset_hour = 0
                next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                next_reset = now.replace(hour=next_reset_hour, minute=0, second=0, microsecond=0)
        else:
            next_reset = now.replace(minute=next_reset_minute, second=0, microsecond=0)
        
        wait_seconds = int((next_reset - now).total_seconds()) + 10  # 10 second buffer
        return max(wait_seconds, 0)
    
    def wait_for_rate_limit_reset(self, access_token: str = None) -> None:
        """
        Wait for rate limit to reset
        
        Args:
            access_token: Access token to check (uses config if not provided)
        """
        can_proceed, wait_seconds = self.check_rate_limit_status(access_token)
        
        if not can_proceed:
            wait_minutes = wait_seconds / 60
            print(f"⏱️  Rate limit reached. Waiting {wait_minutes:.1f} minutes...")
            
            # Wait in chunks to allow for interruption
            for i in range(wait_seconds):
                try:
                    if i % 60 == 0 and i > 0:  # Show progress every minute
                        remaining_minutes = (wait_seconds - i) / 60
                        print(f"   {remaining_minutes:.1f} minutes remaining...")
                    time.sleep(1)
                except KeyboardInterrupt:
                    print("\nRate limit wait interrupted by user")
                    raise
    
    def ensure_authenticated_client(self) -> StravaClient:
        """
        Create authenticated client with rate limit checking
        
        Returns:
            Authenticated StravaClient instance
        """
        # Check if we have credentials
        if not self.config_manager.validate_strava_credentials():
            print("❌ Strava credentials not configured")
            print("\nTo configure:")
            print("1. Go to https://www.strava.com/settings/api")
            print("2. Create an application")
            print("3. Update client_id and client_secret in config.json")
            print("4. Run get_refresh_token.py to get access tokens")
            raise ValueError("Strava credentials not configured")
        
        # Check if we have access token
        if not self.config_manager.has_access_token():
            print("❌ No access token found")
            print("Run get_refresh_token.py to obtain access tokens")
            raise ValueError("No access token configured")
        
        # Check rate limit status
        print("🔍 Checking rate limit status...")
        try:
            can_proceed, wait_seconds = self.check_rate_limit_status()
            if not can_proceed:
                print(f"⏱️  Rate limit reached. Waiting {wait_seconds} seconds...")
                self.wait_for_rate_limit_reset()
        except Exception as e:
            print(f"⚠️  Could not check rate limit status: {e}")
            print("Proceeding anyway...")
        
        # Create and test client
        return self.create_client()


# Convenience functions for backward compatibility
def authenticate_strava(config: Dict[str, Any]) -> StravaClient:
    """
    Authenticate with Strava API (convenience function)
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Authenticated StravaClient instance
    """
    # Create temporary config file for compatibility
    import tempfile
    import json
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        temp_config_file = f.name
    
    try:
        authenticator = StravaAuthenticator(temp_config_file)
        return authenticator.create_client()
    finally:
        import os
        os.unlink(temp_config_file)


def check_rate_limit_status(access_token: str) -> bool:
    """
    Check rate limit status (convenience function)
    
    Args:
        access_token: Access token to check
        
    Returns:
        True if can proceed, False if rate limited
    """
    # Create temporary authenticator without config file
    authenticator = StravaAuthenticator()
    can_proceed, _ = authenticator.check_rate_limit_status(access_token)
    return can_proceed


def create_authenticated_client(config_file: str = "config.json") -> StravaClient:
    """
    Create authenticated Strava client (convenience function)
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Authenticated StravaClient instance
    """
    authenticator = StravaAuthenticator(config_file)
    return authenticator.ensure_authenticated_client()