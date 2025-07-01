#!/usr/bin/env python3

"""
Consolidate individual activity JSON files into a single GPS data file
compatible with generate_heatmap_svg.py
"""

import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any


def load_individual_activity_files(data_dir: str) -> Dict[int, List[List[float]]]:
    """Load all individual activity JSON files and extract GPS coordinates"""
    
    gps_data_dict = {}
    activity_files = glob.glob(os.path.join(data_dir, "activity_*.json"))
    
    if not activity_files:
        print(f"No activity files found in {data_dir}")
        return gps_data_dict
    
    print(f"Found {len(activity_files)} activity files")
    
    for activity_file in sorted(activity_files):
        try:
            with open(activity_file, 'r') as f:
                activity_data = json.load(f)
            
            # Extract GPS coordinates from the activity
            if 'gps_points' in activity_data and activity_data['gps_points']:
                activity_id = activity_data.get('activity_id', 0)
                coords = activity_data['gps_points']
                gps_data_dict[activity_id] = coords
                print(f"  {os.path.basename(activity_file)}: {len(coords)} GPS points")
            else:
                print(f"  {os.path.basename(activity_file)}: No GPS data")
                
        except Exception as e:
            print(f"  Error loading {activity_file}: {e}")
    
    return gps_data_dict


def main():
    print("GPS Data Consolidation Tool")
    print("=" * 30)
    
    # Configuration
    data_dir = "strava_data"
    output_file = os.path.join(data_dir, "gps_data.json")
    
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist")
        return
    
    # Load all individual activity files
    print(f"Loading GPS data from individual activity files in {data_dir}...")
    gps_data_dict = load_individual_activity_files(data_dir)
    
    if not gps_data_dict:
        print("No GPS data found in activity files")
        return
    
    # Save consolidated GPS data
    print(f"\nSaving consolidated GPS data to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(gps_data_dict, f)
    
    # Create latest version link for compatibility
    latest_file = os.path.join(data_dir, "gps_data_latest.json")
    with open(latest_file, 'w') as f:
        json.dump(gps_data_dict, f)
    
    # Calculate total points
    total_points = sum(len(coords) for coords in gps_data_dict.values())
    
    # Summary
    print(f"\n📊 Consolidation Summary:")
    print(f"  Total activities: {len(gps_data_dict):,}")
    print(f"  Total GPS points: {total_points:,}")
    print(f"  Output file: {output_file}")
    print(f"  Latest version: {latest_file}")
    
    # Show geographical bounds
    if gps_data_dict:
        all_points = []
        for coords in gps_data_dict.values():
            all_points.extend(coords)
        
        lats = [point[0] for point in all_points]
        lons = [point[1] for point in all_points]
        
        print(f"\n🌍 Geographical Coverage:")
        print(f"  Latitude range: {min(lats):.6f} to {max(lats):.6f}")
        print(f"  Longitude range: {min(lons):.6f} to {max(lons):.6f}")
    
    print("\nConsolidation complete! You can now run generate_heatmap_svg.py")


if __name__ == "__main__":
    main()