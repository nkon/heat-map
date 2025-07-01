#!/usr/bin/env python3

"""
Strava Common Utilities

Provides common helper functions and utilities used across Strava scripts.
Eliminates duplication of utility code.
"""

import os
import sys
from typing import Dict, Any, List, Set, Optional
from datetime import datetime


# Activity type filters
INDOOR_ACTIVITY_TYPES = {
    'WeightTraining', 'Yoga', 'Workout', 'Crosstraining', 'Elliptical',
    'StairStepper', 'Rowing', 'VirtualRide', 'VirtualRun'
}

GPS_ACTIVITY_TYPES = {
    'Ride', 'Run', 'Hike', 'Walk', 'NordicSki', 'AlpineSki', 'BackcountrySki',
    'MountainBikeRide', 'GravelRide', 'RoadRide', 'TrailRun', 'Swim'
}


def filter_gps_activities(activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter activities that likely have GPS data
    
    Args:
        activities: List of activity dictionaries
        
    Returns:
        List of activities with GPS potential
    """
    gps_activities = []
    
    for activity in activities:
        activity_type = activity.get('type', 'Unknown')
        
        # Skip known indoor activities
        if activity_type in INDOOR_ACTIVITY_TYPES:
            continue
        
        # Include known GPS activities
        if activity_type in GPS_ACTIVITY_TYPES:
            gps_activities.append(activity)
            continue
        
        # For unknown types, include if they have distance > 0
        distance = activity.get('distance', 0)
        if distance and distance > 0:
            gps_activities.append(activity)
    
    return gps_activities


def should_skip_activity(activity: Dict[str, Any]) -> tuple[bool, str]:
    """
    Determine if an activity should be skipped
    
    Args:
        activity: Activity dictionary
        
    Returns:
        Tuple of (should_skip, reason)
    """
    activity_type = activity.get('type', 'Unknown')
    activity_id = activity.get('id', 'Unknown')
    
    # Skip indoor activities
    if activity_type in INDOOR_ACTIVITY_TYPES:
        return True, f"Indoor activity type: {activity_type}"
    
    # Skip activities without distance
    distance = activity.get('distance', 0)
    if not distance or distance <= 0:
        return True, "No distance recorded"
    
    # Skip manual activities (likely no GPS)
    manual = activity.get('manual', False)
    if manual:
        return True, "Manual entry"
    
    return False, ""


def safe_get_activity_name(activity: Dict[str, Any]) -> str:
    """
    Safely extract activity name
    
    Args:
        activity: Activity dictionary
        
    Returns:
        Activity name or default
    """
    name = activity.get('name', '')
    activity_id = activity.get('id', 'unknown')
    
    if not name or name.strip() == '':
        return f"Activity_{activity_id}"
    
    return name.strip()


def extract_date_from_activity(activity: Dict[str, Any]) -> str:
    """
    Extract date string from activity
    
    Args:
        activity: Activity dictionary
        
    Returns:
        Date string in YYYYMMDD format
    """
    start_date = activity.get('start_date', '')
    
    if start_date:
        try:
            # Extract date part and remove separators
            date_part = start_date.split('T')[0].replace('-', '')
            return date_part
        except Exception:
            pass
    
    # Fallback to current date
    return datetime.now().strftime('%Y%m%d')


def format_activity_summary(activity: Dict[str, Any], gps_points_count: int = 0) -> str:
    """
    Format activity summary for display
    
    Args:
        activity: Activity dictionary
        gps_points_count: Number of GPS points
        
    Returns:
        Formatted summary string
    """
    activity_id = activity.get('id', 'Unknown')
    activity_type = activity.get('type', 'Unknown')
    activity_name = safe_get_activity_name(activity)[:30]  # Truncate long names
    date = extract_date_from_activity(activity)
    
    if gps_points_count > 0:
        return f"{activity_id} | {activity_type:12} | {date} | {gps_points_count:5,} pts | {activity_name}"
    else:
        return f"{activity_id} | {activity_type:12} | {date} | {'No GPS':>8} | {activity_name}"


def validate_config_credentials(config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate Strava configuration credentials
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    strava_config = config.get('strava', {})
    
    # Check required fields
    required_fields = ['client_id', 'client_secret']
    for field in required_fields:
        value = strava_config.get(field, '')
        if not value or value == f"YOUR_{field.upper()}":
            issues.append(f"Missing or default {field}")
    
    # Check if access token is configured
    access_token = strava_config.get('access_token', '')
    if not access_token or access_token == "YOUR_ACCESS_TOKEN":
        issues.append("Missing or default access_token")
    
    return len(issues) == 0, issues


def print_config_help() -> None:
    """Print help for configuring Strava credentials"""
    print("🔧 Strava Configuration Required")
    print()
    print("To get Strava API credentials:")
    print("1. Go to https://www.strava.com/settings/api")
    print("2. Create an application")
    print("3. Update client_id and client_secret in config.json")
    print("4. Run get_refresh_token.py to get access tokens")
    print()


def create_activity_filename(activity: Dict[str, Any], max_name_length: int = 50) -> str:
    """
    Create filename for individual activity
    
    Args:
        activity: Activity dictionary
        max_name_length: Maximum length for activity name part
        
    Returns:
        Safe filename
    """
    activity_id = activity.get('id', 'unknown')
    activity_name = safe_get_activity_name(activity)
    date = extract_date_from_activity(activity)
    
    # Make filename safe
    safe_name = make_filename_safe(activity_name, max_name_length)
    
    return f"activity_{date}_{activity_id}_{safe_name}.json"


def make_filename_safe(name: str, max_length: int = 50) -> str:
    """
    Convert string to safe filename
    
    Args:
        name: Original name
        max_length: Maximum length
        
    Returns:
        Safe filename string
    """
    # Keep only safe characters
    safe_chars = []
    for char in name:
        if char.isalnum() or char in ' -_':
            safe_chars.append(char)
        else:
            safe_chars.append('_')  # Replace unsafe chars with underscore
    
    safe_name = ''.join(safe_chars).strip()
    
    # Replace multiple spaces/underscores with single ones
    safe_name = ' '.join(safe_name.split())
    safe_name = '_'.join(safe_name.split('_'))
    
    # Truncate if too long, breaking at word boundary
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
        # Find last space to break at word boundary
        last_space = safe_name.rfind(' ')
        if last_space > max_length // 2:  # Only break if space is in second half
            safe_name = safe_name[:last_space]
    
    # Ensure not empty
    if not safe_name or safe_name.isspace():
        safe_name = "unnamed"
    
    return safe_name


def estimate_activity_count(first_page_activities: List[Dict[str, Any]], 
                          per_page: int, max_years: int = 8) -> int:
    """
    Estimate total number of activities based on first page
    
    Args:
        first_page_activities: Activities from first API page
        per_page: Number of activities per page
        max_years: Maximum years to consider
        
    Returns:
        Estimated total activities
    """
    if not first_page_activities:
        return 0
    
    try:
        # Get oldest activity from first page
        oldest_activity = first_page_activities[-1]
        oldest_date_str = oldest_activity.get('start_date', '')
        
        if oldest_date_str:
            # Parse date
            oldest_date = datetime.fromisoformat(oldest_date_str.replace('Z', '+00:00'))
            now = datetime.now().replace(tzinfo=oldest_date.tzinfo)
            
            days_since_oldest = (now - oldest_date).days
            
            if days_since_oldest > 0:
                # Calculate activities per day from sample
                activities_per_day = len(first_page_activities) / min(days_since_oldest, per_page)
                
                # Estimate total for max_years
                estimated_total = int(activities_per_day * 365 * max_years)
                
                # Cap at reasonable maximum
                return min(estimated_total, 20000)
    
    except Exception:
        pass
    
    # Fallback estimate
    return len(first_page_activities) * 10


def print_script_header(title: str, description: str = None) -> None:
    """
    Print standardized script header
    
    Args:
        title: Script title
        description: Optional description
    """
    print(title)
    print("=" * len(title))
    
    if description:
        print(description)
        print()


def handle_keyboard_interrupt(operation_name: str = "Operation") -> None:
    """
    Handle keyboard interrupt gracefully
    
    Args:
        operation_name: Name of the operation being interrupted
    """
    print(f"\n\n⚠️  {operation_name} interrupted by user (Ctrl+C)")
    print("Exiting gracefully...")
    sys.exit(0)


def check_python_version(min_version: tuple = (3, 8)) -> None:
    """
    Check if Python version meets requirements
    
    Args:
        min_version: Minimum required version tuple
    """
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        min_version_str = '.'.join(map(str, min_version))
        current_version_str = '.'.join(map(str, current_version))
        
        print(f"❌ Python {min_version_str}+ required. Current version: {current_version_str}")
        sys.exit(1)


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure directory exists, creating if necessary
    
    Args:
        directory: Directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"📁 Created directory: {directory}")


def calculate_storage_size(gps_points_count: int) -> str:
    """
    Estimate storage size for GPS points
    
    Args:
        gps_points_count: Number of GPS coordinate pairs
        
    Returns:
        Formatted size estimate
    """
    # Rough estimate: each GPS point is ~50 bytes in JSON
    estimated_bytes = gps_points_count * 50
    
    if estimated_bytes < 1024:
        return f"{estimated_bytes} B"
    elif estimated_bytes < 1024 * 1024:
        return f"{estimated_bytes / 1024:.1f} KB"
    elif estimated_bytes < 1024 * 1024 * 1024:
        return f"{estimated_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{estimated_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_activity_date_range(activities: List[Dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
    """
    Get date range of activities
    
    Args:
        activities: List of activity dictionaries
        
    Returns:
        Tuple of (earliest_date, latest_date) as ISO strings
    """
    if not activities:
        return None, None
    
    dates = []
    for activity in activities:
        start_date = activity.get('start_date')
        if start_date:
            dates.append(start_date)
    
    if not dates:
        return None, None
    
    dates.sort()
    return dates[0], dates[-1]


def format_date_range(start_date: str, end_date: str) -> str:
    """
    Format date range for display
    
    Args:
        start_date: Start date ISO string
        end_date: End date ISO string
        
    Returns:
        Formatted date range
    """
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        start_str = start.strftime('%Y-%m-%d')
        end_str = end.strftime('%Y-%m-%d')
        
        return f"{start_str} to {end_str}"
    except Exception:
        return f"{start_date} to {end_date}"