#!/usr/bin/env python3

import os
import json
from typing import Dict, Any
from heatmap_generator import HeatmapGenerator
from map_data import MapDataProvider
from svg_renderer import SVGRenderer


def load_config() -> Dict[str, Any]:
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Create default config file
    default_config = {
        "data": {
            "input_dir": "strava_data",
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
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Created {config_file}. Please update it with your settings.")
    return default_config


def load_gps_data(config: Dict[str, Any]) -> Dict[int, Any]:
    data_config = config["data"]
    input_dir = data_config["input_dir"]
    
    # Try to load latest file first, then fall back to config file
    latest_file = os.path.join(input_dir, "gps_data_latest.json")
    config_file = os.path.join(input_dir, data_config["gps_data_file"])
    
    gps_data_file = latest_file if os.path.exists(latest_file) else config_file
    
    if not os.path.exists(gps_data_file):
        raise FileNotFoundError(f"GPS data file not found: {gps_data_file}")
    
    print(f"Loading GPS data from: {os.path.basename(gps_data_file)}")
    
    with open(gps_data_file, 'r') as f:
        data = json.load(f)
    
    # Convert string keys back to integers
    return {int(k): v for k, v in data.items()}


def load_athlete_info(config: Dict[str, Any]) -> Dict[str, Any]:
    data_config = config["data"]
    input_dir = data_config["input_dir"]
    
    # Try to load latest file first, then fall back to generic file
    latest_file = os.path.join(input_dir, "athlete_info_latest.json")
    generic_file = os.path.join(input_dir, "athlete_info.json")
    
    athlete_file = latest_file if os.path.exists(latest_file) else generic_file
    
    if os.path.exists(athlete_file):
        print(f"Loading athlete info from: {os.path.basename(athlete_file)}")
        with open(athlete_file, 'r') as f:
            return json.load(f)
    
    return {"firstname": "Unknown", "lastname": "Athlete"}


def main():
    print("Strava Heatmap SVG Generator")
    print("=" * 30)
    
    # Load configuration
    config = load_config()
    
    # Load GPS data
    print("Loading GPS data...")
    try:
        gps_data = load_gps_data(config)
        athlete_info = load_athlete_info(config)
        
        print(f"Loaded GPS data from {len(gps_data)} activities")
        print(f"Athlete: {athlete_info['firstname']} {athlete_info['lastname']}")
        
        if not gps_data:
            print("No GPS data found. Please run download_strava_data.py first.")
            return
            
    except Exception as e:
        print(f"Failed to load GPS data: {e}")
        return
    
    # Generate heatmap
    print("Generating heatmap...")
    try:
        heatmap_gen = HeatmapGenerator()
        heatmap_grid = heatmap_gen.generate_heatmap(gps_data)
        bounds = heatmap_gen.get_bounds()
        
        print(f"Generated heatmap with bounds: {bounds}")
        
    except Exception as e:
        print(f"Failed to generate heatmap: {e}")
        return
    
    # Get map data
    print("Loading map boundaries...")
    try:
        map_provider = MapDataProvider()
        
        # Get world boundaries
        world_data = map_provider.get_world_boundaries()
        filtered_world = map_provider.filter_boundaries_by_bounds(world_data, bounds)
        world_paths = map_provider.get_boundary_paths(filtered_world)
        
        # Get US states if in US bounds
        us_bounds = (24, -125, 50, -66)  # Rough US bounds
        if (bounds[0] >= us_bounds[0] and bounds[1] >= us_bounds[1] and 
            bounds[2] <= us_bounds[2] and bounds[3] <= us_bounds[3]):
            us_data = map_provider.get_us_states()
            filtered_us = map_provider.filter_boundaries_by_bounds(us_data, bounds)
            us_paths = map_provider.get_boundary_paths(filtered_us)
            world_paths.extend(us_paths)
        
        print(f"Loaded {len(world_paths)} boundary paths")
        
    except Exception as e:
        print(f"Failed to load map data: {e}")
        print("Continuing without map boundaries...")
        world_paths = []
    
    # Create SVG
    print("Creating SVG...")
    try:
        output_config = config["output"]
        style_config = config["style"]
        
        renderer = SVGRenderer(
            width=output_config["width"],
            height=output_config["height"]
        )
        
        # Create SVG with bounds
        svg_root = renderer.create_svg(bounds)
        
        # Add boundaries
        if world_paths:
            renderer.add_boundary_paths(
                world_paths,
                stroke_color=style_config["boundary_color"],
                stroke_width=style_config["boundary_width"]
            )
        
        # Add GPS tracks
        renderer.add_gps_tracks(
            gps_data,
            stroke_color=style_config["track_color"],
            stroke_width=style_config["track_width"]
        )
        
        # Add title and legend
        athlete_name = f"{athlete_info['firstname']} {athlete_info['lastname']}"
        renderer.add_title(f"{athlete_name}'s Strava Activity Heatmap")
        renderer.add_legend()
        
        # Save SVG
        output_file = output_config["filename"]
        renderer.save_svg(output_file)
        
        print(f"SVG saved as: {output_file}")
        
    except Exception as e:
        print(f"Failed to create SVG: {e}")
        return
    
    print("\nHeatmap generation complete!")


if __name__ == "__main__":
    main()