#!/usr/bin/env python3

"""
GPS Data Consolidation Tool

Consolidates individual activity JSON files into unified GPS data files
compatible with heatmap generation. Refactored to use centralized utilities.
"""

from strava_config import StravaConfig
from strava_files import StravaFileManager
from strava_progress import StravaProgressReporter
from strava_utils import handle_keyboard_interrupt
from heatmap_utils import (
    validate_gps_data_structure,
    format_gps_summary,
    calculate_gps_bounds
)


def main():
    """Main GPS data consolidation process"""
    try:
        # Initialize utilities
        config_manager = StravaConfig()
        progress_reporter = StravaProgressReporter("GPS Data Consolidation Tool")
        
        # Start operation
        progress_reporter.start_operation(
            "Consolidates individual activity JSON files into unified GPS data files\n"
            "compatible with heatmap generation"
        )
        
        # Load configuration and setup file manager
        config_manager.load()
        file_manager = StravaFileManager(config_manager.get_output_dir())
        
        # Load individual activity files
        print("📂 Loading individual activity files...")
        try:
            activities = file_manager.load_individual_activities()
            
            if not activities:
                progress_reporter.add_error("No individual activity files found")
                print("💡 Tip: Run download_individual_activities.py first to create activity files")
                return
            
            progress_reporter.log_file_operation(
                "loaded", 
                f"{len(activities)} individual activity files"
            )
            
            # Log each activity for progress tracking
            for activity in activities:
                mock_activity_info = {
                    'id': activity.get('activity_id', 'unknown'),
                    'type': activity.get('activity_type', 'Unknown'),
                    'name': activity.get('activity_name', 'Unnamed')
                }
                gps_count = len(activity.get('gps_points', []))
                progress_reporter.log_activity_processed(mock_activity_info, gps_count)
            
        except Exception as e:
            progress_reporter.add_error(f"Failed to load activity files: {e}")
            return
        
        # Consolidate GPS data
        print("\n🔄 Consolidating GPS data...")
        try:
            gps_data_dict = file_manager.consolidate_gps_data_from_activities(activities)
            
            if not gps_data_dict:
                progress_reporter.add_error("No GPS data found in activity files")
                return
            
            progress_reporter.log_file_operation(
                "consolidated", 
                f"GPS data from {len(gps_data_dict)} activities"
            )
            
        except Exception as e:
            progress_reporter.add_error(f"Failed to consolidate GPS data: {e}")
            return
        
        # Validate consolidated data
        print("✅ Validating consolidated GPS data...")
        is_valid, issues = validate_gps_data_structure(gps_data_dict)
        if not is_valid:
            for issue in issues[:5]:  # Show first 5 issues
                progress_reporter.add_warning(f"GPS data validation: {issue}")
            if len(issues) > 5:
                progress_reporter.add_warning(f"... and {len(issues) - 5} more validation issues")
        
        # Show GPS data summary
        print("\n" + format_gps_summary(gps_data_dict))
        
        # Save consolidated GPS data
        print("\n💾 Saving consolidated GPS data...")
        try:
            # Save with timestamp and latest versions
            timestamped_path, latest_path = file_manager.save_gps_data(gps_data_dict)
            
            progress_reporter.log_file_operation("saved", timestamped_path)
            progress_reporter.log_file_operation("saved", latest_path)
            
        except Exception as e:
            progress_reporter.add_error(f"Failed to save GPS data: {e}")
            return
        
        # Calculate and show geographical coverage
        bounds = calculate_gps_bounds(gps_data_dict)
        min_lat, max_lat, min_lon, max_lon = bounds
        
        print(f"\n🌍 Geographical Coverage:")
        print(f"  Latitude range: {min_lat:.6f}° to {max_lat:.6f}°")
        print(f"  Longitude range: {min_lon:.6f}° to {max_lon:.6f}°")
        print(f"  Coverage area: {abs(max_lat - min_lat):.3f}° × {abs(max_lon - min_lon):.3f}°")
        
        # Show final summary
        additional_stats = {
            'Output directory': file_manager.output_dir,
            'Consolidated activities': len(gps_data_dict),
            'Geographic span': f"{abs(max_lat - min_lat):.3f}° × {abs(max_lon - min_lon):.3f}°",
            'Data validation': "✅ Passed" if is_valid else f"⚠️ {len(issues)} issues found"
        }
        
        progress_reporter.show_summary(additional_stats)
        
        print(f"\n🎉 GPS data consolidation complete!")
        print("💡 You can now run generate_heatmap_svg.py to create your heatmap")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt("GPS Data Consolidation")
    except Exception as e:
        print(f"❌ GPS data consolidation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()