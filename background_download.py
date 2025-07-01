#!/usr/bin/env python3

"""
Background Strava Data Downloader
Downloads 8 years of GPS data with rate limiting, progress tracking, and resume capability
"""

import os
import json
import time
import logging
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from strava_client import StravaClient


class BackgroundDownloader:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.client = None
        self.stop_requested = False
        self.state_file = "download_state.json"
        self.log_file = "background_download.log"
        self.downloaded_activities: Set[int] = set()
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def setup_logging(self):
        """Setup logging to both file and console"""
        self.logger = logging.getLogger('background_downloader')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def signal_handler(self, signum, frame):
        """Handle interrupt signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        self.stop_requested = True
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not os.path.exists(self.config_file):
            self.create_default_config()
            
        with open(self.config_file, 'r') as f:
            return json.load(f)
            
    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "strava": {
                "client_id": "YOUR_CLIENT_ID",
                "client_secret": "YOUR_CLIENT_SECRET",
                "access_token": "YOUR_ACCESS_TOKEN",
                "refresh_token": "YOUR_REFRESH_TOKEN"
            },
            "data": {
                "output_dir": "strava_data",
                "gps_data_file": "gps_data.json"
            },
            "download": {
                "max_years": 8,
                "batch_size": 50,
                "retry_attempts": 3,
                "retry_delay": 300,
                "save_progress_interval": 10
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        print(f"Created {self.config_file}. Please update with your Strava API credentials.")
        
    def load_state(self) -> Dict[str, Any]:
        """Load download state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.downloaded_activities = set(state.get('downloaded_activities', []))
                    return state
            except Exception as e:
                self.logger.warning(f"Failed to load state file: {e}")
                
        return {
            'downloaded_activities': [],
            'last_page': 1,
            'total_activities': 0,
            'total_gps_points': 0,
            'start_time': None,
            'last_update': None
        }
        
    def save_state(self, state: Dict[str, Any]):
        """Save download state to file"""
        try:
            state['downloaded_activities'] = list(self.downloaded_activities)
            state['last_update'] = datetime.now().isoformat()
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            
    def authenticate(self) -> bool:
        """Authenticate with Strava API"""
        try:
            strava_config = self.config["strava"]
            
            self.client = StravaClient(
                client_id=strava_config["client_id"],
                client_secret=strava_config["client_secret"],
                access_token=strava_config.get("access_token"),
                refresh_token=strava_config.get("refresh_token"),
                config_file=self.config_file
            )
            
            # Test authentication
            athlete = self.client.get_athlete()
            self.logger.info(f"Authenticated as: {athlete['firstname']} {athlete['lastname']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
            
    def get_activity_count_estimate(self) -> int:
        """Estimate total number of activities to download"""
        try:
            # Get first page to estimate total
            activities = self.client.get_activities(per_page=200, page=1)
            if not activities:
                return 0
                
            # Estimate based on activity frequency
            oldest_activity = activities[-1]
            oldest_date = datetime.fromisoformat(oldest_activity['start_date'].replace('Z', '+00:00'))
            days_since_oldest = (datetime.now().replace(tzinfo=oldest_date.tzinfo) - oldest_date).days
            
            if days_since_oldest > 0:
                activities_per_day = len(activities) / min(days_since_oldest, 200)
                max_years = self.config.get("download", {}).get("max_years", 8)
                estimated_total = int(activities_per_day * 365 * max_years)
                return min(estimated_total, 10000)  # Cap at reasonable maximum
            
            return len(activities)
            
        except Exception as e:
            self.logger.warning(f"Failed to estimate activity count: {e}")
            return 1000  # Default estimate
            
    def download_activity_safely(self, activity: Dict[str, Any], output_dir: str) -> Optional[Dict[str, Any]]:
        """Download a single activity with error handling and retries"""
        activity_id = activity['id']
        
        # Skip if already downloaded
        if activity_id in self.downloaded_activities:
            return None
            
        max_attempts = self.config.get("download", {}).get("retry_attempts", 3)
        retry_delay = self.config.get("download", {}).get("retry_delay", 300)
        
        for attempt in range(max_attempts):
            if self.stop_requested:
                return None
                
            try:
                activity_type = activity.get('type', 'Unknown')
                activity_date = activity.get('start_date', '').split('T')[0]
                activity_name = activity.get('name', f'Activity_{activity_id}')
                
                # Skip non-GPS activities
                if activity_type in ['WeightTraining', 'Yoga', 'Workout', 'Crosstraining']:
                    self.downloaded_activities.add(activity_id)
                    return None
                    
                self.logger.info(f"Downloading activity {activity_id} ({activity_type}) - {activity_date} - Attempt {attempt + 1}")
                
                gps_points = self.client.download_activity_gps_data(activity_id)
                
                if gps_points:
                    # Create safe filename
                    safe_name = ''.join(c for c in activity_name if c.isalnum() or c in ' -_').strip()[:50]
                    filename = f"activity_{activity_date.replace('-', '')}_{activity_id}_{safe_name}.json"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save activity data
                    activity_data = {
                        'activity_id': activity_id,
                        'activity_type': activity_type,
                        'activity_name': activity_name,
                        'start_date': activity['start_date'],
                        'gps_points': gps_points,
                        'total_points': len(gps_points),
                        'download_timestamp': datetime.now().isoformat()
                    }
                    
                    with open(filepath, 'w') as f:
                        json.dump(activity_data, f, indent=2)
                        
                    self.downloaded_activities.add(activity_id)
                    self.logger.info(f"✓ Saved {len(gps_points)} GPS points to {filename}")
                    
                    return {
                        'filename': filename,
                        'filepath': filepath,
                        'activity_type': activity_type,
                        'gps_points_count': len(gps_points)
                    }
                else:
                    self.downloaded_activities.add(activity_id)
                    self.logger.info(f"Activity {activity_id} has no GPS data")
                    return None
                    
            except Exception as e:
                self.logger.warning(f"Failed to download activity {activity_id} (attempt {attempt + 1}): {e}")
                
                if attempt < max_attempts - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    # Sleep in small chunks to allow for interruption
                    for _ in range(retry_delay):
                        if self.stop_requested:
                            return None
                        time.sleep(1)
                else:
                    self.logger.error(f"Failed to download activity {activity_id} after {max_attempts} attempts")
                    
        return None
        
    def run(self):
        """Main download loop"""
        self.logger.info("Starting background Strava data download")
        self.logger.info("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            return
            
        # Create output directory
        output_dir = self.config["data"]["output_dir"]
        os.makedirs(output_dir, exist_ok=True)
        
        # Load previous state
        state = self.load_state()
        if state['start_time'] is None:
            state['start_time'] = datetime.now().isoformat()
            
        # Estimate total activities
        if state['total_activities'] == 0:
            state['total_activities'] = self.get_activity_count_estimate()
            self.logger.info(f"Estimated total activities: {state['total_activities']}")
            
        # Download activities
        page = state.get('last_page', 1)
        downloaded_count = len(self.downloaded_activities)
        total_gps_points = state.get('total_gps_points', 0)
        save_interval = self.config.get("download", {}).get("save_progress_interval", 10)
        
        self.logger.info(f"Resuming from page {page}, {downloaded_count} activities already downloaded")
        
        try:
            while not self.stop_requested:
                self.logger.info(f"Fetching activities page {page}...")
                
                activities = self.client.get_activities(per_page=200, page=page)
                if not activities:
                    self.logger.info("No more activities found. Download complete!")
                    break
                    
                page_start_time = time.time()
                page_downloaded = 0
                page_points = 0
                
                for i, activity in enumerate(activities):
                    if self.stop_requested:
                        break
                        
                    result = self.download_activity_safely(activity, output_dir)
                    if result:
                        page_downloaded += 1
                        page_points += result['gps_points_count']
                        total_gps_points += result['gps_points_count']
                        
                    # Save progress periodically
                    if (i + 1) % save_interval == 0:
                        state['last_page'] = page
                        state['total_gps_points'] = total_gps_points
                        self.save_state(state)
                        
                        progress = (len(self.downloaded_activities) / state['total_activities']) * 100
                        self.logger.info(f"Progress: {progress:.1f}% ({len(self.downloaded_activities)}/{state['total_activities']} activities)")
                        
                if self.stop_requested:
                    break
                    
                # Page summary
                page_time = time.time() - page_start_time
                self.logger.info(f"Page {page} complete: {page_downloaded} new activities, {page_points:,} GPS points in {page_time:.1f}s")
                
                # Update state
                state['last_page'] = page + 1
                state['total_gps_points'] = total_gps_points
                self.save_state(state)
                
                page += 1
                
                # Rate limiting info
                self.logger.info(f"Rate limit usage: {self.client.rate_limiter.short_term_requests}/100 (15min), "
                                f"{self.client.rate_limiter.daily_requests}/1000 (daily)")
                
        except KeyboardInterrupt:
            self.logger.info("Download interrupted by user")
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            # Final state save
            state['total_gps_points'] = total_gps_points
            self.save_state(state)
            
            # Final summary
            total_time = datetime.now() - datetime.fromisoformat(state['start_time'])
            self.logger.info("\n" + "=" * 60)
            self.logger.info("DOWNLOAD SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"Total runtime: {total_time}")
            self.logger.info(f"Activities downloaded: {len(self.downloaded_activities)}")
            self.logger.info(f"Total GPS points: {total_gps_points:,}")
            self.logger.info(f"Files saved in: {output_dir}")
            self.logger.info(f"State saved in: {self.state_file}")
            self.logger.info(f"Log saved in: {self.log_file}")
            
            if self.stop_requested:
                self.logger.info("Download was stopped gracefully. Run again to resume.")
            else:
                self.logger.info("Download completed successfully!")


def main():
    """Main entry point"""
    print("Strava Background Data Downloader")
    print("Press Ctrl+C to stop gracefully and resume later")
    print("=" * 60)
    
    downloader = BackgroundDownloader()
    downloader.run()


if __name__ == "__main__":
    main()