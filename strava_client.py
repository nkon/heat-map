import requests
import json
import os
from typing import List, Dict, Any, Optional
import time
from datetime import datetime, timedelta


class StravaRateLimiter:
    def __init__(self):
        self.short_term_requests = 0
        self.short_term_reset = datetime.now() + timedelta(minutes=15)
        self.daily_requests = 0
        self.daily_reset = datetime.now() + timedelta(days=1)
        
    def can_make_request(self) -> bool:
        now = datetime.now()
        
        # Reset counters if time has passed
        if now >= self.short_term_reset:
            self.short_term_requests = 0
            self.short_term_reset = now + timedelta(minutes=15)
            
        if now >= self.daily_reset:
            self.daily_requests = 0
            self.daily_reset = now + timedelta(days=1)
        
        # Check limits (15 min: 100 requests, daily: 1000 requests)
        return self.short_term_requests < 100 and self.daily_requests < 1000
    
    def wait_if_needed(self):
        while not self.can_make_request():
            now = datetime.now()
            if self.short_term_requests >= 100:
                wait_seconds = (self.short_term_reset - now).total_seconds()
                if wait_seconds > 0:
                    print(f"Rate limit reached. Waiting {wait_seconds:.0f} seconds...")
                    # Sleep in 1-second chunks to allow for keyboard interrupts
                    total_sleep = int(wait_seconds + 1)
                    for i in range(total_sleep):
                        try:
                            time.sleep(1)
                            if i % 10 == 0 and i > 0:  # Show countdown every 10 seconds
                                remaining = total_sleep - i
                                print(f"  {remaining} seconds remaining...")
                        except KeyboardInterrupt:
                            print("\nRate limit wait interrupted by user")
                            raise
                else:
                    # Reset time has passed, update counters
                    self.short_term_requests = 0
                    self.short_term_reset = now + timedelta(minutes=15)
            elif self.daily_requests >= 1000:
                wait_seconds = (self.daily_reset - now).total_seconds()
                if wait_seconds > 0:
                    print(f"Daily limit reached. Waiting {wait_seconds:.0f} seconds...")
                    # Sleep in 1-second chunks to allow for keyboard interrupts
                    total_sleep = int(wait_seconds + 1)
                    for i in range(total_sleep):
                        try:
                            time.sleep(1)
                            if i % 60 == 0 and i > 0:  # Show countdown every minute
                                remaining = total_sleep - i
                                hours = remaining // 3600
                                minutes = (remaining % 3600) // 60
                                print(f"  {hours}h {minutes}m remaining...")
                        except KeyboardInterrupt:
                            print("\nDaily limit wait interrupted by user")
                            raise
                else:
                    # Reset time has passed, update counters
                    self.daily_requests = 0
                    self.daily_reset = now + timedelta(days=1)
            else:
                # Safety break - should not happen
                break
    
    def record_request(self):
        self.short_term_requests += 1
        self.daily_requests += 1


class StravaClient:
    def __init__(self, client_id: str, client_secret: str, access_token: str = None, 
                 refresh_token: str = None, config_file: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.config_file = config_file
        self.base_url = "https://www.strava.com/api/v3"
        self.rate_limiter = StravaRateLimiter()
        
    def get_authorization_url(self, redirect_uri: str, scope: str = "activity:read_all") -> str:
        return (f"https://www.strava.com/oauth/authorize?"
                f"client_id={self.client_id}&"
                f"response_type=code&"
                f"redirect_uri={redirect_uri}&"
                f"approval_prompt=force&"
                f"scope={scope}")
    
    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        token_url = "https://www.strava.com/oauth/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data['access_token']
        return token_data
    
    def refresh_token_method(self, refresh_token: str) -> Dict[str, Any]:
        token_url = "https://www.strava.com/oauth/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data['access_token']
        self.refresh_token = token_data.get('refresh_token', refresh_token)
        return token_data
    
    def _refresh_access_token(self):
        if not self.refresh_token:
            raise ValueError("Refresh token not available")
        
        token_data = self.refresh_token_method(self.refresh_token)
        
        # Save updated tokens to config file if available
        if self.config_file:
            self._save_tokens_to_config(token_data)
    
    def _save_tokens_to_config(self, token_data: Dict[str, Any]):
        if not self.config_file or not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            config['strava']['access_token'] = token_data['access_token']
            config['strava']['refresh_token'] = token_data.get('refresh_token', self.refresh_token)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            print(f"Updated tokens saved to {self.config_file}")
            
        except Exception as e:
            print(f"Failed to save tokens to config: {e}")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.access_token:
            raise ValueError("Access token not set")
        
        # Check rate limits and wait if necessary
        self.rate_limiter.wait_if_needed()
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # Check if token is expired (401 Unauthorized)
            if response.status_code == 401 and self.refresh_token:
                print("Access token expired, refreshing...")
                self._refresh_access_token()
                headers = {'Authorization': f'Bearer {self.access_token}'}
                # Retry the request with new token
                response = requests.get(url, headers=headers, params=params)
            
            response.raise_for_status()
            
            # Record successful request for rate limiting
            self.rate_limiter.record_request()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit exceeded
                print("Rate limit exceeded by server. Waiting 60 seconds...")
                # Sleep in 1-second chunks to allow for keyboard interrupts
                for i in range(60):
                    try:
                        time.sleep(1)
                        if i % 10 == 0 and i > 0:  # Show countdown every 10 seconds
                            remaining = 60 - i
                            print(f"  {remaining} seconds remaining...")
                    except KeyboardInterrupt:
                        print("\nServer rate limit wait interrupted by user")
                        raise
                return self._make_request(endpoint, params)
            raise
    
    def get_athlete(self) -> Dict[str, Any]:
        return self._make_request("athlete")
    
    def get_activities(self, per_page: int = 200, page: int = 1) -> List[Dict[str, Any]]:
        params = {
            'per_page': per_page,
            'page': page
        }
        return self._make_request("athlete/activities", params)
    
    def get_all_activities(self) -> List[Dict[str, Any]]:
        all_activities = []
        page = 1
        
        while True:
            activities = self.get_activities(per_page=200, page=page)
            if not activities:
                break
            
            all_activities.extend(activities)
            page += 1
            # Rate limiting is now handled in _make_request
            
        return all_activities
    
    def get_activity_streams(self, activity_id: int, types: List[str] = None) -> Dict[str, Any]:
        if types is None:
            types = ['latlng', 'time', 'altitude', 'velocity_smooth', 'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']
        
        type_string = ','.join(types)
        endpoint = f"activities/{activity_id}/streams/{type_string}"
        params = {
            'key_by_type': 'true',
            'keys': type_string
        }
        
        return self._make_request(endpoint, params)
    
    def download_activity_gps_data(self, activity_id: int) -> List[List[float]]:
        try:
            streams = self.get_activity_streams(activity_id, ['latlng'])
            if 'latlng' in streams and streams['latlng']['data']:
                return streams['latlng']['data']
            return []
        except Exception as e:
            print(f"Error downloading GPS data for activity {activity_id}: {e}")
            return []
    
    def download_all_gps_data(self) -> Dict[int, List[List[float]]]:
        activities = self.get_all_activities()
        gps_data = {}
        
        for activity in activities:
            activity_id = activity['id']
            activity_type = activity.get('type', 'Unknown')
            
            # Skip non-GPS activities
            if activity_type in ['WeightTraining', 'Yoga', 'Workout']:
                continue
                
            print(f"Downloading GPS data for activity {activity_id} ({activity_type})")
            gps_points = self.download_activity_gps_data(activity_id)
            
            if gps_points:
                gps_data[activity_id] = gps_points
            
            # Rate limiting is now handled in _make_request
            
        return gps_data
    
    def download_individual_activity_gps_data(self, output_dir: str) -> Dict[str, Any]:
        """Download GPS data for each activity and save to individual files"""
        activities = self.get_all_activities()
        file_info = {}
        
        for activity in activities:
            activity_id = activity['id']
            activity_type = activity.get('type', 'Unknown')
            activity_date = activity.get('start_date', '').split('T')[0]  # Extract date part
            activity_name = activity.get('name', f'Activity_{activity_id}')
            
            # Skip non-GPS activities
            if activity_type in ['WeightTraining', 'Yoga', 'Workout']:
                continue
                
            print(f"Downloading GPS data for activity {activity_id} ({activity_type}) - {activity_date}")
            gps_points = self.download_activity_gps_data(activity_id)
            
            if gps_points:
                # Create filename with date and activity info
                safe_name = ''.join(c for c in activity_name if c.isalnum() or c in ' -_').strip()[:50]
                filename = f"activity_{activity_date}_{activity_id}_{safe_name}.json"
                filepath = os.path.join(output_dir, filename)
                
                # Save individual activity file
                activity_data = {
                    'activity_id': activity_id,
                    'activity_type': activity_type,
                    'activity_name': activity_name,
                    'start_date': activity['start_date'],
                    'gps_points': gps_points,
                    'total_points': len(gps_points)
                }
                
                with open(filepath, 'w') as f:
                    json.dump(activity_data, f, indent=2)
                
                file_info[activity_id] = {
                    'filename': filename,
                    'filepath': filepath,
                    'activity_type': activity_type,
                    'activity_name': activity_name,
                    'start_date': activity['start_date'],
                    'gps_points_count': len(gps_points)
                }
                
                print(f"  Saved {len(gps_points)} GPS points to {filename}")
            
        return file_info