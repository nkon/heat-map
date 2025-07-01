#!/usr/bin/env python3

"""
Strava Progress Reporting Utility

Centralizes progress reporting, statistics display, and summary generation.
Eliminates duplication of progress tracking code across scripts.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict


class StravaProgressReporter:
    """Handles progress reporting and statistics for Strava operations"""
    
    def __init__(self, title: str = "Strava Operation"):
        self.title = title
        self.start_time = datetime.now()
        self.stats = defaultdict(int)
        self.activity_types = defaultdict(int)
        self.errors = []
        self.warnings = []
        
    def start_operation(self, description: str = None) -> None:
        """
        Start a new operation with header display
        
        Args:
            description: Optional description of the operation
        """
        self.start_time = datetime.now()
        
        print(self.title)
        print("=" * len(self.title))
        
        if description:
            print(description)
            print()
        
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def log_activity_processed(self, activity: Dict[str, Any], gps_points: int = 0, 
                             skipped: bool = False, error: str = None) -> None:
        """
        Log processing of an activity
        
        Args:
            activity: Activity data dictionary
            gps_points: Number of GPS points processed
            skipped: Whether the activity was skipped
            error: Error message if processing failed
        """
        activity_type = activity.get('type', 'Unknown')
        activity_id = activity.get('id', 'Unknown')
        activity_name = activity.get('name', 'Unnamed')
        
        self.stats['total_activities'] += 1
        self.activity_types[activity_type] += 1
        
        if error:
            self.stats['failed_activities'] += 1
            self.errors.append(f"Activity {activity_id} ({activity_type}): {error}")
            print(f"❌ Failed: {activity_id} - {activity_type} - {error}")
        elif skipped:
            self.stats['skipped_activities'] += 1
            print(f"⏭️  Skipped: {activity_id} - {activity_type} - {activity_name}")
        else:
            self.stats['processed_activities'] += 1
            self.stats['total_gps_points'] += gps_points
            
            if gps_points > 0:
                self.stats['activities_with_gps'] += 1
                print(f"✅ Processed: {activity_id} - {activity_type} - {gps_points:,} GPS points")
            else:
                print(f"📍 No GPS: {activity_id} - {activity_type}")
    
    def log_rate_limit_info(self, client: Any) -> None:
        """
        Log rate limit usage information
        
        Args:
            client: StravaClient instance with rate limiter
        """
        if hasattr(client, 'rate_limiter'):
            rate_limiter = client.rate_limiter
            short_term = getattr(rate_limiter, 'short_term_requests', 0)
            daily = getattr(rate_limiter, 'daily_requests', 0)
            
            print(f"📊 Rate limit usage: {short_term}/100 (15min), {daily}/1000 (daily)")
            
            # Warn if approaching limits
            if short_term >= 90:
                self.warnings.append(f"Approaching short-term rate limit: {short_term}/100")
            if daily >= 900:
                self.warnings.append(f"Approaching daily rate limit: {daily}/1000")
    
    def log_page_progress(self, page: int, activities_count: int, 
                         processed_count: int = 0, skipped_count: int = 0) -> None:
        """
        Log progress for a page of activities
        
        Args:
            page: Page number
            activities_count: Number of activities in this page
            processed_count: Number of activities processed in this page
            skipped_count: Number of activities skipped in this page
        """
        print(f"\n📄 Page {page}: {activities_count} activities")
        if processed_count > 0 or skipped_count > 0:
            print(f"   Processed: {processed_count}, Skipped: {skipped_count}")
    
    def log_batch_progress(self, current: int, total: int, item_type: str = "items") -> None:
        """
        Log progress for batch operations
        
        Args:
            current: Current item number
            total: Total number of items
            item_type: Type of items being processed
        """
        if total > 0:
            percentage = (current / total) * 100
            print(f"🔄 Progress: {current}/{total} {item_type} ({percentage:.1f}%)")
    
    def show_summary(self, additional_stats: Dict[str, Any] = None) -> None:
        """
        Display operation summary
        
        Args:
            additional_stats: Additional statistics to include
        """
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 OPERATION SUMMARY")
        print("=" * 60)
        
        # Time information
        print(f"⏱️  Duration: {self._format_duration(duration)}")
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏁 Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Activity statistics
        if self.stats['total_activities'] > 0:
            print("📈 Activity Statistics:")
            print(f"   Total activities: {self.stats['total_activities']:,}")
            print(f"   Successfully processed: {self.stats['processed_activities']:,}")
            print(f"   Activities with GPS: {self.stats['activities_with_gps']:,}")
            print(f"   Skipped: {self.stats['skipped_activities']:,}")
            print(f"   Failed: {self.stats['failed_activities']:,}")
            print(f"   Total GPS points: {self.stats['total_gps_points']:,}")
            print()
        
        # Activity types breakdown
        if self.activity_types:
            print("🏃 Activity Types:")
            for activity_type, count in sorted(self.activity_types.items(), 
                                             key=lambda x: x[1], reverse=True):
                print(f"   {activity_type}: {count}")
            print()
        
        # Additional statistics
        if additional_stats:
            print("📊 Additional Statistics:")
            for key, value in additional_stats.items():
                if isinstance(value, (int, float)):
                    if isinstance(value, int) and value > 1000:
                        print(f"   {key}: {value:,}")
                    else:
                        print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")
            print()
        
        # Warnings
        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
        
        # Errors
        if self.errors:
            print("❌ Errors:")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   ... and {len(self.errors) - 5} more errors")
            print()
        
        # Performance statistics
        if self.stats['total_activities'] > 0:
            activities_per_second = self.stats['total_activities'] / duration.total_seconds()
            print(f"⚡ Performance: {activities_per_second:.2f} activities/second")
            
            if self.stats['total_gps_points'] > 0:
                points_per_second = self.stats['total_gps_points'] / duration.total_seconds()
                print(f"📍 GPS processing: {points_per_second:,.0f} points/second")
    
    def _format_duration(self, duration: timedelta) -> str:
        """
        Format duration for display
        
        Args:
            duration: Duration timedelta
            
        Returns:
            Formatted duration string
        """
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def add_warning(self, message: str) -> None:
        """
        Add a warning message
        
        Args:
            message: Warning message
        """
        self.warnings.append(message)
        print(f"⚠️  Warning: {message}")
    
    def add_error(self, message: str) -> None:
        """
        Add an error message
        
        Args:
            message: Error message
        """
        self.errors.append(message)
        print(f"❌ Error: {message}")
    
    def log_file_operation(self, operation: str, filepath: str, 
                          size: int = None, count: int = None) -> None:
        """
        Log file operation
        
        Args:
            operation: Operation type (saved, loaded, etc.)
            filepath: File path
            size: File size in bytes (optional)
            count: Number of items in file (optional)
        """
        message = f"📁 {operation.capitalize()}: {filepath}"
        
        if size is not None:
            message += f" ({self._format_file_size(size)})"
        
        if count is not None:
            message += f" [{count:,} items]"
        
        print(message)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size for display
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def create_progress_callback(self, total_items: int, 
                               update_interval: int = 10) -> callable:
        """
        Create a progress callback function
        
        Args:
            total_items: Total number of items to process
            update_interval: How often to show progress (every N items)
            
        Returns:
            Callback function
        """
        def progress_callback(current_item: int, item_data: Any = None) -> None:
            if current_item % update_interval == 0 or current_item == total_items:
                self.log_batch_progress(current_item, total_items)
        
        return progress_callback


# Convenience functions for backward compatibility
def show_download_summary(activities_processed: int, gps_points: int, 
                         output_dir: str, duration: timedelta = None) -> None:
    """
    Show download summary (convenience function)
    
    Args:
        activities_processed: Number of activities processed
        gps_points: Total GPS points
        output_dir: Output directory
        duration: Operation duration
    """
    reporter = StravaProgressReporter("Download Summary")
    reporter.stats['processed_activities'] = activities_processed
    reporter.stats['total_gps_points'] = gps_points
    
    if duration:
        reporter.start_time = datetime.now() - duration
    
    additional_stats = {
        'Output directory': output_dir
    }
    
    reporter.show_summary(additional_stats)


def create_progress_reporter(title: str) -> StravaProgressReporter:
    """
    Create progress reporter (convenience function)
    
    Args:
        title: Operation title
        
    Returns:
        StravaProgressReporter instance
    """
    return StravaProgressReporter(title)