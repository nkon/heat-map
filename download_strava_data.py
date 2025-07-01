#!/usr/bin/env python3

"""
Strava GPS Data Downloader

Downloads GPS data from Strava API and saves to individual activity files.
Refactored to use centralized utilities for configuration, authentication, 
file operations, and progress reporting.
"""

from strava_config import StravaConfig
from strava_auth import StravaAuthenticator
from strava_files import StravaFileManager
from strava_progress import StravaProgressReporter
from strava_utils import handle_keyboard_interrupt


def main():
    """Main download process"""
    try:
        # Initialize utilities
        config_manager = StravaConfig()
        authenticator = StravaAuthenticator()
        progress_reporter = StravaProgressReporter("Strava GPS Data Downloader")
        
        # Start operation
        progress_reporter.start_operation(
            "Downloads GPS data from Strava API and saves to individual activity files"
        )
        
        # Load configuration and setup file manager
        config_manager.load()
        file_manager = StravaFileManager(config_manager.get_output_dir())
        
        # Authenticate and create client
        print("🔐 Authenticating with Strava...")
        client = authenticator.ensure_authenticated_client()
        
        # Get athlete info for summary
        athlete = client.get_athlete()
        
        # Download GPS data to individual files
        print("\n📥 Downloading GPS data from Strava...")
        try:
            file_info = client.download_individual_activity_gps_data(file_manager.output_dir)
            
            if not file_info:
                print("❌ No GPS data found. Make sure you have activities with GPS tracks.")
                return
            
            print(f"✅ Downloaded GPS data from {len(file_info)} activities")
            
            # Process file info for progress reporting
            for activity_id, info in file_info.items():
                # Create mock activity data for progress reporter
                mock_activity = {
                    'id': activity_id,
                    'type': info.get('activity_type', 'Unknown'),
                    'name': info.get('filename', f'Activity_{activity_id}')
                }
                progress_reporter.log_activity_processed(
                    mock_activity, 
                    info['gps_points_count']
                )
            
            # Save athlete info with file manager
            athlete_timestamped, athlete_latest = file_manager.save_athlete_info(athlete)
            progress_reporter.log_file_operation("saved", athlete_timestamped)
            progress_reporter.log_file_operation("saved", athlete_latest)
            
            # Save activities summary
            summary_timestamped, _ = file_manager.save_json_file(
                file_info, 
                f"activities_summary_{file_manager.generate_timestamp()}.json"
            )
            progress_reporter.log_file_operation("saved", summary_timestamped, count=len(file_info))
            
            # Log rate limit usage
            progress_reporter.log_rate_limit_info(client)
            
            # Show final summary
            additional_stats = {
                'Output directory': file_manager.output_dir,
                'Individual files saved': len(file_info),
                'Latest files created': 2  # athlete_latest + summary_latest
            }
            
            progress_reporter.show_summary(additional_stats)
            
        except Exception as e:
            progress_reporter.add_error(f"Failed to download GPS data: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print(f"\n🎉 Data download complete! Files saved in: {file_manager.output_dir}")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt("Download")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()