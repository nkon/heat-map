#!/usr/bin/env python3

"""
Strava File Operations Utility

Centralizes file saving patterns, timestamping, and directory management.
Eliminates duplication of file handling code across scripts.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class StravaFileManager:
    """Manages file operations for Strava data"""
    
    def __init__(self, output_dir: str = "strava_data"):
        self.output_dir = output_dir
        self.ensure_output_dir()
    
    def ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_timestamp(self, format_type: str = "file") -> str:
        """
        Generate timestamp string
        
        Args:
            format_type: "file" for filenames, "iso" for ISO format
            
        Returns:
            Timestamp string
        """
        now = datetime.now()
        if format_type == "file":
            return now.strftime("%Y%m%d_%H%M%S")
        elif format_type == "iso":
            return now.isoformat()
        elif format_type == "date":
            return now.strftime("%Y%m%d")
        else:
            return now.strftime("%Y%m%d_%H%M%S")
    
    def save_json_file(self, data: Any, filename: str, create_latest: bool = True) -> str:
        """
        Save data as JSON file
        
        Args:
            data: Data to save
            filename: Filename (without path)
            create_latest: Also create a *_latest.json version
            
        Returns:
            Full path to saved file
        """
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Create latest version if requested
        if create_latest and not filename.endswith('_latest.json'):
            base_name = filename.rsplit('.', 1)[0]  # Remove .json
            latest_filename = f"{base_name}_latest.json"
            latest_filepath = os.path.join(self.output_dir, latest_filename)
            
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_json_file(self, filename: str, try_latest: bool = True) -> Any:
        """
        Load data from JSON file
        
        Args:
            filename: Filename to load
            try_latest: Try *_latest.json version first
            
        Returns:
            Loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Try latest version first
        if try_latest and not filename.endswith('_latest.json'):
            base_name = filename.rsplit('.', 1)[0]  # Remove .json
            latest_filename = f"{base_name}_latest.json"
            latest_filepath = os.path.join(self.output_dir, latest_filename)
            
            if os.path.exists(latest_filepath):
                with open(latest_filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Try original filename
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        raise FileNotFoundError(f"Could not find {filename} or latest version in {self.output_dir}")
    
    def save_athlete_info(self, athlete_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Save athlete information with timestamp
        
        Args:
            athlete_data: Athlete data from Strava API
            
        Returns:
            Tuple of (timestamped_file_path, latest_file_path)
        """
        timestamp = self.generate_timestamp()
        timestamped_filename = f"athlete_info_{timestamp}.json"
        
        timestamped_path = self.save_json_file(athlete_data, timestamped_filename, create_latest=False)
        latest_path = self.save_json_file(athlete_data, "athlete_info_latest.json", create_latest=False)
        
        return timestamped_path, latest_path
    
    def save_gps_data(self, gps_data: Dict[str, List[List[float]]], prefix: str = "gps_data") -> Tuple[str, str]:
        """
        Save GPS data with timestamp
        
        Args:
            gps_data: GPS data dictionary {activity_id: [[lat, lon], ...]}
            prefix: Filename prefix
            
        Returns:
            Tuple of (timestamped_file_path, latest_file_path)
        """
        timestamp = self.generate_timestamp()
        timestamped_filename = f"{prefix}_{timestamp}.json"
        
        timestamped_path = self.save_json_file(gps_data, timestamped_filename, create_latest=False)
        latest_path = self.save_json_file(gps_data, f"{prefix}_latest.json", create_latest=False)
        
        return timestamped_path, latest_path
    
    def save_individual_activity(self, activity_data: Dict[str, Any]) -> str:
        """
        Save individual activity data with date-based naming
        
        Args:
            activity_data: Activity data including GPS points
            
        Returns:
            Path to saved file
        """
        activity_id = activity_data['activity_id']
        activity_name = activity_data.get('activity_name', f'Activity_{activity_id}')
        start_date = activity_data.get('start_date', '')
        
        # Extract date from start_date
        if start_date:
            date_part = start_date.split('T')[0].replace('-', '')
        else:
            date_part = self.generate_timestamp("date")
        
        # Create safe filename
        safe_name = self.make_safe_filename(activity_name)
        filename = f"activity_{date_part}_{activity_id}_{safe_name}.json"
        
        return self.save_json_file(activity_data, filename, create_latest=False)
    
    def make_safe_filename(self, name: str, max_length: int = 50) -> str:
        """
        Convert string to safe filename
        
        Args:
            name: Original name
            max_length: Maximum filename length
            
        Returns:
            Safe filename string
        """
        # Keep only alphanumeric characters, spaces, hyphens, and underscores
        safe_name = ''.join(c for c in name if c.isalnum() or c in ' -_').strip()
        
        # Replace multiple spaces with single space
        safe_name = ' '.join(safe_name.split())
        
        # Truncate if too long
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length].rsplit(' ', 1)[0]  # Break at word boundary
        
        # Ensure not empty
        if not safe_name:
            safe_name = "unnamed"
        
        return safe_name
    
    def load_individual_activities(self, pattern: str = "activity_*.json") -> List[Dict[str, Any]]:
        """
        Load all individual activity files
        
        Args:
            pattern: Glob pattern for activity files
            
        Returns:
            List of activity data dictionaries
        """
        import glob
        
        file_pattern = os.path.join(self.output_dir, pattern)
        activity_files = glob.glob(file_pattern)
        activities = []
        
        for filepath in activity_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
                    activities.append(activity_data)
            except Exception as e:
                print(f"⚠️  Failed to load {filepath}: {e}")
        
        return activities
    
    def consolidate_gps_data_from_activities(self, activities: List[Dict[str, Any]]) -> Dict[str, List[List[float]]]:
        """
        Consolidate GPS data from individual activities
        
        Args:
            activities: List of activity data dictionaries
            
        Returns:
            Consolidated GPS data {activity_id: [[lat, lon], ...]}
        """
        consolidated = {}
        
        for activity in activities:
            activity_id = activity.get('activity_id')
            gps_points = activity.get('gps_points', [])
            
            if activity_id and gps_points:
                consolidated[str(activity_id)] = gps_points
        
        return consolidated
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get file information
        
        Args:
            filename: Filename to check
            
        Returns:
            File info dictionary or None if file doesn't exist
        """
        filepath = os.path.join(self.output_dir, filename)
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        return {
            'path': filepath,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'created': datetime.fromtimestamp(stat.st_ctime)
        }
    
    def list_files(self, pattern: str = "*") -> List[str]:
        """
        List files in output directory
        
        Args:
            pattern: Glob pattern
            
        Returns:
            List of filenames (without path)
        """
        import glob
        
        file_pattern = os.path.join(self.output_dir, pattern)
        full_paths = glob.glob(file_pattern)
        
        # Return just the filenames
        return [os.path.basename(path) for path in full_paths]
    
    def clean_old_files(self, pattern: str, keep_count: int = 5) -> List[str]:
        """
        Clean old files, keeping only the most recent
        
        Args:
            pattern: Glob pattern for files to clean
            keep_count: Number of recent files to keep
            
        Returns:
            List of deleted filenames
        """
        import glob
        
        file_pattern = os.path.join(self.output_dir, pattern)
        files = glob.glob(file_pattern)
        
        if len(files) <= keep_count:
            return []
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Delete older files
        deleted = []
        for filepath in files[keep_count:]:
            try:
                os.remove(filepath)
                deleted.append(os.path.basename(filepath))
            except Exception as e:
                print(f"⚠️  Failed to delete {filepath}: {e}")
        
        return deleted


# Convenience functions for backward compatibility
def save_athlete_info(athlete_data: Dict[str, Any], output_dir: str = "strava_data") -> Tuple[str, str]:
    """
    Save athlete information (convenience function)
    
    Args:
        athlete_data: Athlete data from Strava API
        output_dir: Output directory
        
    Returns:
        Tuple of (timestamped_file_path, latest_file_path)
    """
    file_manager = StravaFileManager(output_dir)
    return file_manager.save_athlete_info(athlete_data)


def save_gps_data(gps_data: Dict[str, List[List[float]]], output_dir: str = "strava_data") -> Tuple[str, str]:
    """
    Save GPS data (convenience function)
    
    Args:
        gps_data: GPS data dictionary
        output_dir: Output directory
        
    Returns:
        Tuple of (timestamped_file_path, latest_file_path)
    """
    file_manager = StravaFileManager(output_dir)
    return file_manager.save_gps_data(gps_data)


def load_gps_data(output_dir: str = "strava_data") -> Dict[str, List[List[float]]]:
    """
    Load GPS data (convenience function)
    
    Args:
        output_dir: Output directory
        
    Returns:
        GPS data dictionary
    """
    file_manager = StravaFileManager(output_dir)
    return file_manager.load_json_file("gps_data.json")