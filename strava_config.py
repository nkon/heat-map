#!/usr/bin/env python3

"""
Strava Configuration Management Utility

Centralizes configuration loading, validation, and default creation across all Strava scripts.
Eliminates duplication of config management code.
"""

import os
import json
from typing import Dict, Any, Optional


class StravaConfig:
    """Manages Strava application configuration"""
    
    DEFAULT_CONFIG = {
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
        "output": {
            "filename": "strava_heatmap.svg",
            "width": 1200,
            "height": 800
        },
        "style": {
            "track_color": "#dc3545",
            "track_width": "1.5",
            "boundary_color": "#dee2e6",
            "boundary_width": "0.5"
        },
        "download": {
            "max_years": 8,
            "batch_size": 50,
            "retry_attempts": 3,
            "retry_delay": 300,
            "save_progress_interval": 10
        }
    }
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self._config: Optional[Dict[str, Any]] = None
    
    def load(self, create_if_missing: bool = True) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Args:
            create_if_missing: Create default config if file doesn't exist
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist and create_if_missing is False
            ValueError: If config file contains invalid JSON
        """
        if not os.path.exists(self.config_file):
            if create_if_missing:
                self.create_default()
            else:
                raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            return self._config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {self.config_file}: {e}")
    
    def create_default(self) -> None:
        """Create default configuration file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        
        print(f"Created {self.config_file}. Please update with your Strava API credentials.")
        print("\nTo get Strava API credentials:")
        print("1. Go to https://www.strava.com/settings/api")
        print("2. Create an application")
        print("3. Update client_id and client_secret in config.json")
        print("4. Run get_refresh_token.py to get access tokens")
    
    def save(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file
        
        Args:
            config: Configuration dictionary to save
        """
        self._config = config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., "strava.client_id")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if self._config is None:
            self._config = self.load()
        
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., "strava.access_token")
            value: Value to set
        """
        if self._config is None:
            self._config = self.load()
        
        keys = key_path.split('.')
        current = self._config
        
        # Navigate to parent dictionary
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
    
    def validate_strava_credentials(self) -> bool:
        """
        Check if Strava credentials are configured
        
        Returns:
            True if credentials are set, False otherwise
        """
        client_id = self.get("strava.client_id")
        client_secret = self.get("strava.client_secret")
        
        return (client_id and client_id != "YOUR_CLIENT_ID" and
                client_secret and client_secret != "YOUR_CLIENT_SECRET")
    
    def has_access_token(self) -> bool:
        """
        Check if access token is configured
        
        Returns:
            True if access token is set, False otherwise
        """
        access_token = self.get("strava.access_token")
        return access_token and access_token != "YOUR_ACCESS_TOKEN"
    
    def update_tokens(self, access_token: str, refresh_token: str = None) -> None:
        """
        Update Strava tokens in configuration
        
        Args:
            access_token: New access token
            refresh_token: New refresh token (optional)
        """
        self.set("strava.access_token", access_token)
        if refresh_token:
            self.set("strava.refresh_token", refresh_token)
        self.save(self._config)
    
    def get_strava_config(self) -> Dict[str, str]:
        """
        Get Strava-specific configuration
        
        Returns:
            Dictionary containing Strava API credentials
        """
        return {
            "client_id": self.get("strava.client_id"),
            "client_secret": self.get("strava.client_secret"),
            "access_token": self.get("strava.access_token"),
            "refresh_token": self.get("strava.refresh_token")
        }
    
    def get_output_dir(self) -> str:
        """Get output directory, creating if it doesn't exist"""
        output_dir = self.get("data.output_dir", "strava_data")
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary"""
        if self._config is None:
            self._config = self.load()
        return self._config


# Convenience functions for backward compatibility
def load_config(config_file: str = "config.json", create_if_missing: bool = True) -> Dict[str, Any]:
    """
    Load configuration from file (convenience function)
    
    Args:
        config_file: Path to configuration file
        create_if_missing: Create default config if file doesn't exist
        
    Returns:
        Configuration dictionary
    """
    config_manager = StravaConfig(config_file)
    return config_manager.load(create_if_missing)


def create_default_config(config_file: str = "config.json") -> None:
    """
    Create default configuration file (convenience function)
    
    Args:
        config_file: Path to configuration file
    """
    config_manager = StravaConfig(config_file)
    config_manager.create_default()


def save_config(config: Dict[str, Any], config_file: str = "config.json") -> None:
    """
    Save configuration to file (convenience function)
    
    Args:
        config: Configuration dictionary to save
        config_file: Path to configuration file
    """
    config_manager = StravaConfig(config_file)
    config_manager.save(config)