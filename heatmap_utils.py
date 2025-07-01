#!/usr/bin/env python3

"""
Heatmap Generation Utilities

Provides common utilities for heatmap generation, data validation,
and geographic operations used across heatmap scripts.
"""

from typing import Dict, List, Tuple, Any, Optional
import os


def validate_gps_data_structure(gps_data: Any) -> Tuple[bool, List[str]]:
    """
    Validate GPS data structure
    
    Args:
        gps_data: GPS data to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if not isinstance(gps_data, dict):
        issues.append("GPS data must be a dictionary")
        return False, issues
    
    if len(gps_data) == 0:
        issues.append("GPS data is empty")
        return False, issues
    
    # Check structure of entries
    for activity_id, points in gps_data.items():
        try:
            # Validate activity ID can be converted to string
            str(activity_id)
        except Exception:
            issues.append(f"Invalid activity ID: {activity_id}")
            continue
        
        if not isinstance(points, list):
            issues.append(f"Activity {activity_id}: GPS points must be a list")
            continue
        
        if len(points) == 0:
            issues.append(f"Activity {activity_id}: No GPS points found")
            continue
        
        # Validate a few sample points
        sample_size = min(5, len(points))
        for i in range(sample_size):
            point = points[i]
            if not isinstance(point, list) or len(point) != 2:
                issues.append(f"Activity {activity_id}: Invalid GPS point format at index {i}")
                break
            
            try:
                lat, lon = float(point[0]), float(point[1])
                if not (-90 <= lat <= 90):
                    issues.append(f"Activity {activity_id}: Invalid latitude {lat} at index {i}")
                    break
                if not (-180 <= lon <= 180):
                    issues.append(f"Activity {activity_id}: Invalid longitude {lon} at index {i}")
                    break
            except (ValueError, TypeError):
                issues.append(f"Activity {activity_id}: Non-numeric coordinates at index {i}")
                break
    
    return len(issues) == 0, issues


def calculate_gps_bounds(gps_data: Dict[str, List[List[float]]]) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box of all GPS points
    
    Args:
        gps_data: GPS data dictionary
        
    Returns:
        Tuple of (min_lat, max_lat, min_lon, max_lon)
    """
    all_lats = []
    all_lons = []
    
    for points in gps_data.values():
        for lat, lon in points:
            all_lats.append(lat)
            all_lons.append(lon)
    
    if not all_lats:
        return 0.0, 0.0, 0.0, 0.0
    
    return min(all_lats), max(all_lats), min(all_lons), max(all_lons)


def count_total_gps_points(gps_data: Dict[str, List[List[float]]]) -> int:
    """
    Count total number of GPS points across all activities
    
    Args:
        gps_data: GPS data dictionary
        
    Returns:
        Total number of GPS points
    """
    return sum(len(points) for points in gps_data.values())


def filter_gps_data_by_bounds(gps_data: Dict[str, List[List[float]]], 
                             min_lat: float, max_lat: float,
                             min_lon: float, max_lon: float) -> Dict[str, List[List[float]]]:
    """
    Filter GPS data to only include points within bounds
    
    Args:
        gps_data: GPS data dictionary
        min_lat, max_lat, min_lon, max_lon: Bounding box
        
    Returns:
        Filtered GPS data dictionary
    """
    filtered_data = {}
    
    for activity_id, points in gps_data.items():
        filtered_points = []
        for lat, lon in points:
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                filtered_points.append([lat, lon])
        
        if filtered_points:  # Only include activities with points in bounds
            filtered_data[activity_id] = filtered_points
    
    return filtered_data


def calculate_heatmap_resolution(gps_data: Dict[str, List[List[float]]], 
                               target_width: int = 1200, 
                               target_height: int = 800) -> Tuple[int, int, float]:
    """
    Calculate optimal heatmap resolution based on GPS data density
    
    Args:
        gps_data: GPS data dictionary
        target_width: Target SVG width in pixels
        target_height: Target SVG height in pixels
        
    Returns:
        Tuple of (grid_width, grid_height, points_per_pixel)
    """
    if not gps_data:
        return target_width // 4, target_height // 4, 0.0
    
    min_lat, max_lat, min_lon, max_lon = calculate_gps_bounds(gps_data)
    total_points = count_total_gps_points(gps_data)
    
    # Calculate geographic span
    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    
    if lat_span == 0 or lon_span == 0:
        return target_width // 4, target_height // 4, 0.0
    
    # Calculate aspect ratio
    aspect_ratio = lon_span / lat_span
    
    # Adjust grid size to maintain aspect ratio
    if aspect_ratio > target_width / target_height:
        # Wider than target, fit to width
        grid_width = target_width // 4  # Reduce resolution for performance
        grid_height = int(grid_width / aspect_ratio)
    else:
        # Taller than target, fit to height
        grid_height = target_height // 4
        grid_width = int(grid_height * aspect_ratio)
    
    # Ensure minimum size
    grid_width = max(grid_width, 100)
    grid_height = max(grid_height, 100)
    
    # Calculate density
    points_per_pixel = total_points / (grid_width * grid_height)
    
    return grid_width, grid_height, points_per_pixel


def format_gps_summary(gps_data: Dict[str, List[List[float]]]) -> str:
    """
    Format GPS data summary for display
    
    Args:
        gps_data: GPS data dictionary
        
    Returns:
        Formatted summary string
    """
    if not gps_data:
        return "No GPS data available"
    
    activity_count = len(gps_data)
    total_points = count_total_gps_points(gps_data)
    min_lat, max_lat, min_lon, max_lon = calculate_gps_bounds(gps_data)
    
    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    
    summary = f"""GPS Data Summary:
  Activities: {activity_count:,}
  Total GPS points: {total_points:,}
  Geographic bounds:
    Latitude: {min_lat:.4f}° to {max_lat:.4f}° (span: {lat_span:.4f}°)
    Longitude: {min_lon:.4f}° to {max_lon:.4f}° (span: {lon_span:.4f}°)
  Average points per activity: {total_points / activity_count:.1f}"""
    
    return summary


def estimate_processing_time(gps_data: Dict[str, List[List[float]]], 
                           grid_width: int, grid_height: int) -> str:
    """
    Estimate processing time for heatmap generation
    
    Args:
        gps_data: GPS data dictionary
        grid_width: Heatmap grid width
        grid_height: Heatmap grid height
        
    Returns:
        Estimated time string
    """
    total_points = count_total_gps_points(gps_data)
    grid_cells = grid_width * grid_height
    
    # Rough estimation based on operations per point and grid size
    # These are empirical estimates that can be tuned
    operations_per_point = 50  # Coordinate transformation, grid mapping, etc.
    operations_per_cell = 10   # Grid processing, normalization, etc.
    operations_per_second = 1000000  # Rough estimate of Python operations/sec
    
    estimated_seconds = (total_points * operations_per_point + 
                        grid_cells * operations_per_cell) / operations_per_second
    
    if estimated_seconds < 1:
        return "< 1 second"
    elif estimated_seconds < 60:
        return f"~{estimated_seconds:.0f} seconds"
    else:
        minutes = estimated_seconds / 60
        return f"~{minutes:.1f} minutes"


def validate_heatmap_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate heatmap generation configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required sections
    required_sections = ['data', 'output', 'style']
    for section in required_sections:
        if section not in config:
            issues.append(f"Missing required config section: {section}")
    
    # Validate data section
    if 'data' in config:
        data_config = config['data']
        required_data_fields = ['input_dir', 'gps_data_file']
        for field in required_data_fields:
            if field not in data_config:
                issues.append(f"Missing required data config field: {field}")
    
    # Validate output section
    if 'output' in config:
        output_config = config['output']
        required_output_fields = ['filename', 'width', 'height']
        for field in required_output_fields:
            if field not in output_config:
                issues.append(f"Missing required output config field: {field}")
        
        # Validate dimensions
        if 'width' in output_config:
            try:
                width = int(output_config['width'])
                if width <= 0:
                    issues.append("Output width must be positive")
            except (ValueError, TypeError):
                issues.append("Output width must be a number")
        
        if 'height' in output_config:
            try:
                height = int(output_config['height'])
                if height <= 0:
                    issues.append("Output height must be positive")
            except (ValueError, TypeError):
                issues.append("Output height must be a number")
    
    # Validate style section
    if 'style' in config:
        style_config = config['style']
        required_style_fields = ['track_color', 'track_width']
        for field in required_style_fields:
            if field not in style_config:
                issues.append(f"Missing required style config field: {field}")
    
    return len(issues) == 0, issues


def create_cache_directory(cache_dir: str) -> str:
    """
    Create cache directory if it doesn't exist
    
    Args:
        cache_dir: Cache directory path
        
    Returns:
        Absolute path to cache directory
    """
    abs_cache_dir = os.path.abspath(cache_dir)
    os.makedirs(abs_cache_dir, exist_ok=True)
    return abs_cache_dir


def safe_filename_for_bounds(min_lat: float, max_lat: float, 
                           min_lon: float, max_lon: float) -> str:
    """
    Create safe filename based on geographic bounds
    
    Args:
        min_lat, max_lat, min_lon, max_lon: Geographic bounds
        
    Returns:
        Safe filename string
    """
    # Round to reasonable precision and replace dots with underscores
    lat_min_str = f"{min_lat:.2f}".replace('.', '_').replace('-', 'n')
    lat_max_str = f"{max_lat:.2f}".replace('.', '_').replace('-', 'n')
    lon_min_str = f"{min_lon:.2f}".replace('.', '_').replace('-', 'w')
    lon_max_str = f"{max_lon:.2f}".replace('.', '_').replace('-', 'w')
    
    return f"bounds_{lat_min_str}_to_{lat_max_str}_x_{lon_min_str}_to_{lon_max_str}"