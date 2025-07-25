#!/usr/bin/env python3

"""
Strava Heatmap SVG Generator

Generates SVG heatmaps from Strava GPS data with geographic boundaries.
Refactored to use centralized utilities for configuration, file operations,
progress reporting, and data validation.
"""

import argparse
import json
from heatmap_generator import HeatmapGenerator
from map_data import MapDataProvider
from svg_renderer import SVGRenderer
from strava_config import StravaConfig
from strava_files import StravaFileManager
from strava_progress import StravaProgressReporter
from strava_utils import handle_keyboard_interrupt
from heatmap_utils import (
    validate_gps_data_structure, 
    validate_heatmap_config,
    format_gps_summary,
    calculate_gps_bounds,
    estimate_processing_time,
    calculate_heatmap_resolution,
    filter_gps_data_by_region
)


def main():
    """Main heatmap generation process"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate SVG heatmaps from Strava GPS data with geographic boundaries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Region filtering options:
  --region all              Generate heatmap for all GPS data (default)
  --region japan            Generate heatmap for Japan only
  --region usa              Generate heatmap for USA only  
  --region minnesota        Generate heatmap for Minnesota only
  --region saint_paul_100km Generate heatmap within 100km of Saint Paul, MN

Examples:
  python generate_heatmap_svg.py
  python generate_heatmap_svg.py --region japan
  python generate_heatmap_svg.py --region saint_paul_100km
        '''
    )
    
    parser.add_argument(
        '--region', 
        choices=['all', 'japan', 'usa', 'minnesota', 'saint_paul_100km'],
        default='all',
        help='Filter GPS data by geographic region (default: all)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize utilities
        config_manager = StravaConfig()
        progress_reporter = StravaProgressReporter("Strava Heatmap SVG Generator")
        
        # Start operation
        progress_reporter.start_operation(
            "Generates SVG heatmaps from Strava GPS data with geographic boundaries"
        )
        
        # Load and validate configuration
        print("🔧 Loading configuration...")
        config = config_manager.load()
        
        # Validate heatmap-specific configuration
        is_valid_config, config_issues = validate_heatmap_config(config)
        if not is_valid_config:
            for issue in config_issues:
                progress_reporter.add_error(f"Configuration error: {issue}")
            return
        
        # Setup file manager
        file_manager = StravaFileManager(config_manager.get_output_dir())
        
        # Load GPS data
        print("📊 Loading GPS data...")
        try:
            data_config = config["data"]
            gps_data = file_manager.load_json_file(data_config["gps_data_file"])
            
            # Convert string keys to integers for backward compatibility
            if gps_data and isinstance(next(iter(gps_data.keys())), str):
                gps_data = {int(k): v for k, v in gps_data.items()}
            
            # Load athlete info
            try:
                athlete_info = file_manager.load_json_file("athlete_info.json")
            except FileNotFoundError:
                athlete_info = {"firstname": "Unknown", "lastname": "Athlete"}
                progress_reporter.add_warning("Athlete info not found, using defaults")
            
            progress_reporter.log_file_operation("loaded", f"GPS data ({len(gps_data)} activities)")
            
        except FileNotFoundError as e:
            progress_reporter.add_error(f"GPS data not found: {e}")
            print("💡 Tip: Run download_strava_data.py or consolidate_gps_data.py first")
            return
        except Exception as e:
            progress_reporter.add_error(f"Failed to load GPS data: {e}")
            return
        
        # Validate GPS data structure
        print("✅ Validating GPS data...")
        is_valid_gps, gps_issues = validate_gps_data_structure(gps_data)
        if not is_valid_gps:
            for issue in gps_issues[:5]:  # Show first 5 issues
                progress_reporter.add_error(f"GPS data error: {issue}")
            if len(gps_issues) > 5:
                progress_reporter.add_error(f"... and {len(gps_issues) - 5} more GPS data issues")
            return
        
        if not gps_data:
            progress_reporter.add_error("No valid GPS data found")
            return
        
        # Apply region filtering if specified
        if args.region != 'all':
            print(f"\n🌏 Filtering GPS data for region: {args.region}...")
            original_count = len(gps_data)
            gps_data = filter_gps_data_by_region(gps_data, args.region)
            filtered_count = len(gps_data)
            
            if not gps_data:
                progress_reporter.add_error(f"No GPS data found in region '{args.region}'")
                return
            
            print(f"  Filtered from {original_count} to {filtered_count} activities")
            progress_reporter.log_file_operation("filtered", f"GPS data ({filtered_count} activities in {args.region})")
        
        # Show GPS data summary
        print("\n" + format_gps_summary(gps_data))
        
        # Calculate optimal resolution and estimate processing time
        output_config = config["output"]
        grid_width, grid_height, density = calculate_heatmap_resolution(
            gps_data, 
            output_config["width"], 
            output_config["height"]
        )
        
        processing_time = estimate_processing_time(gps_data, grid_width, grid_height)
        print(f"\n📈 Heatmap settings:")
        print(f"  Grid resolution: {grid_width} x {grid_height}")
        print(f"  Point density: {density:.1f} points per grid cell")
        print(f"  Estimated processing time: {processing_time}")
        
        # Generate heatmap
        print("\n🔥 Generating heatmap...")
        try:
            heatmap_gen = HeatmapGenerator()
            heatmap_grid = heatmap_gen.generate_heatmap(gps_data)
            bounds = heatmap_gen.get_bounds()
            
            progress_reporter.log_file_operation(
                "generated", 
                f"heatmap grid ({heatmap_grid.shape[0]}x{heatmap_grid.shape[1]})"
            )
            print(f"✅ Generated heatmap with bounds: {bounds}")
            
            # Expand bounds for USA region to include eastern states like Maine (excluding Alaska and Hawaii)
            if args.region in ['usa', 'all']:
                min_lat, min_lon, max_lat, max_lon = bounds
                # Extend to cover contiguous 48 states only (exclude Alaska and Hawaii)
                extended_min_lat = max(24, min_lat)    # Southern border (exclude Hawaii)
                extended_max_lat = min(49, max_lat)    # Northern border (exclude Alaska)
                extended_min_lon = max(-125, min_lon)  # Western border (exclude Alaska)
                extended_max_lon = max(-66, max_lon)   # Include Maine and eastern states
                bounds = (extended_min_lat, extended_min_lon, extended_max_lat, extended_max_lon)
                print(f"🗺️  Extended bounds for contiguous USA (excluding Alaska/Hawaii): {bounds}")
            
        except Exception as e:
            progress_reporter.add_error(f"Failed to generate heatmap: {e}")
            return
        
        # Load detailed map boundaries
        print("\n🗺️  Loading geographic boundaries...")
        try:
            map_provider = MapDataProvider()
            boundary_data = map_provider.get_detailed_boundaries(bounds)
            
            # Remove Minnesota city boundaries for minnesota and saint_paul_100km regions
            if args.region in ['minnesota', 'saint_paul_100km'] and 'minnesota_cities' in boundary_data:
                print(f"  Removing Minnesota city boundaries for {args.region} region...")
                del boundary_data['minnesota_cities']
            
            progress_reporter.log_file_operation(
                "loaded", 
                f"geographic boundaries ({sum(len(paths) for paths in boundary_data.values())} paths)"
            )
            
        except Exception as e:
            progress_reporter.add_warning(f"Failed to load map boundaries: {e}")
            progress_reporter.add_warning("Continuing without geographic boundaries")
            boundary_data = {}
        
        # Create SVG
        print("\n🎨 Creating SVG visualization...")
        try:
            style_config = config["style"]
            
            renderer = SVGRenderer(
                width=output_config["width"],
                height=output_config["height"]
            )
            
            # Determine projection type based on region
            projection_type = 'equirectangular'  # default
            if args.region in ['minnesota', 'saint_paul_100km']:
                projection_type = 'utm'
                print(f"  Using UTM Zone 15N projection for {args.region} region...")
            elif args.region in ['usa', 'all']:
                projection_type = 'albers'
                print(f"  Using Albers Equal Area Conic projection for {args.region} region...")
            else:
                print(f"  Using equirectangular projection...")
            
            # Create SVG with bounds and background color
            renderer.create_svg(bounds, style_config["background_color"], projection_type)
            
            # Add detailed boundary lines based on configuration
            boundary_config = config.get("boundaries", {})
            
            # World boundaries (coastlines) - skip for Japan/USA regions (use detailed boundaries instead)
            if boundary_data.get('world') and boundary_config.get("world", {}).get("enabled", True):
                # Skip world boundaries if we're in Japan or USA regions (use detailed boundaries instead)
                skip_world = (map_provider.is_japan_region(bounds) or map_provider.is_usa_region(bounds))
                if not skip_world:
                    world_config = boundary_config["world"]
                    print(f"  Adding {len(boundary_data['world'])} world boundary lines...")
                    renderer.add_boundary_paths(
                        boundary_data['world'],
                        stroke_color=world_config.get("color", "#000000"),
                        stroke_width=world_config.get("width", "1.0")
                    )
                else:
                    print("  Skipping world boundaries (using detailed regional boundaries instead)...")
            
            # Japan prefecture boundaries
            if boundary_data.get('japan_prefectures') and boundary_config.get("japan", {}).get("prefectures", {}).get("enabled", True):
                japan_config = boundary_config["japan"]["prefectures"]
                print(f"  Adding {len(boundary_data['japan_prefectures'])} Japan prefecture boundaries...")
                renderer.add_boundary_paths(
                    boundary_data['japan_prefectures'],
                    stroke_color=japan_config.get("color", "#666666"),
                    stroke_width=japan_config.get("width", "0.5")
                )
            
            # US state boundaries
            if boundary_data.get('us_states') and boundary_config.get("usa", {}).get("states", {}).get("enabled", True):
                usa_config = boundary_config["usa"]["states"]
                print(f"  Adding {len(boundary_data['us_states'])} US state boundaries...")
                renderer.add_boundary_paths(
                    boundary_data['us_states'],
                    stroke_color=usa_config.get("color", "#666666"),
                    stroke_width=usa_config.get("width", "0.5")
                )
            
            # Minnesota city boundaries
            if boundary_data.get('minnesota_cities') and boundary_config.get("usa", {}).get("minnesota_cities", {}).get("enabled", True):
                mn_config = boundary_config["usa"]["minnesota_cities"]
                print(f"  Adding {len(boundary_data['minnesota_cities'])} Minnesota city boundaries...")
                renderer.add_boundary_paths(
                    boundary_data['minnesota_cities'],
                    stroke_color=mn_config.get("color", "#999999"),
                    stroke_width=mn_config.get("width", "0.3")
                )
            
            # Lakes and water bodies
            if boundary_data.get('lakes'):
                lakes_enabled = (boundary_config.get("japan", {}).get("lakes", {}).get("enabled", True) or 
                               boundary_config.get("usa", {}).get("lakes", {}).get("enabled", True))
                if lakes_enabled:
                    # Use Japan lake config if in Japan region, otherwise USA lake config
                    if map_provider.is_japan_region(bounds):
                        lake_config = boundary_config.get("japan", {}).get("lakes", {})
                    else:
                        lake_config = boundary_config.get("usa", {}).get("lakes", {})
                    
                    print(f"  Adding {len(boundary_data['lakes'])} lake boundaries...")
                    renderer.add_boundary_paths(
                        boundary_data['lakes'],
                        stroke_color=lake_config.get("color", "#000000"),
                        stroke_width=lake_config.get("width", "0.3")
                    )
            
            # Add GPS tracks
            print(f"  Adding GPS tracks from {len(gps_data)} activities...")
            renderer.add_gps_tracks(
                gps_data,
                stroke_color=style_config["track_color"],
                stroke_width=style_config["track_width"],
                opacity=style_config["track_opacity"]
            )
            
            # Add state parks if enabled and we're in a Minnesota region
            if args.region in ['minnesota', 'saint_paul_100km']:
                parks_config = boundary_config.get("usa", {}).get("state_parks", {})
                if parks_config.get("enabled", False):
                    try:
                        parks_file = parks_config.get("data_file", "map_cache/minnesota_state_parks.json")
                        print(f"  Loading state parks from {parks_file}...")
                        
                        with open(parks_file, 'r') as f:
                            parks_data = json.load(f)
                        
                        # Get individual park settings
                        park_settings = config.get("minnesota_state_parks", {})
                        
                        if parks_data.get("features"):
                            # Filter parks based on individual settings
                            enabled_parks = []
                            for park in parks_data["features"]:
                                park_name = park.get("properties", {}).get("name", "")
                                if park_settings.get(park_name, True):  # Default to True if not specified
                                    enabled_parks.append(park)
                            
                            if enabled_parks:
                                print(f"  Adding {len(enabled_parks)} state parks (filtered from {len(parks_data['features'])} total)...")
                                renderer.add_state_parks(
                                    enabled_parks,
                                    stroke_color=parks_config.get("color", "#ff0000"),
                                    fill_color=parks_config.get("fill", "none"),
                                    radius=parks_config.get("radius", 20),
                                    stroke_width=parks_config.get("stroke_width", 2)
                                )
                            else:
                                print("  No state parks enabled in configuration")
                        else:
                            print("  No state parks found in data file")
                    except FileNotFoundError:
                        progress_reporter.add_warning(f"State parks file not found: {parks_file}")
                    except Exception as e:
                        progress_reporter.add_warning(f"Failed to load state parks: {e}")
                else:
                    print("  State parks rendering disabled in configuration")
            
            # Add national parks if enabled and we're in a USA region
            if args.region in ['usa', 'all', 'minnesota', 'saint_paul_100km']:
                parks_config = boundary_config.get("usa", {}).get("national_parks", {})
                if parks_config.get("enabled", False):
                    try:
                        parks_file = parks_config.get("data_file", "map_cache/us_national_parks.json")
                        print(f"  Loading national parks from {parks_file}...")
                        
                        with open(parks_file, 'r') as f:
                            parks_data = json.load(f)
                        
                        # Get individual park settings
                        park_settings = config.get("us_national_parks", {})
                        
                        if parks_data.get("features"):
                            # Filter parks based on individual settings
                            enabled_parks = []
                            for park in parks_data["features"]:
                                park_name = park.get("properties", {}).get("name", "")
                                if park_settings.get(park_name, True):  # Default to True if not specified
                                    enabled_parks.append(park)
                            
                            if enabled_parks:
                                print(f"  Adding {len(enabled_parks)} national parks (filtered from {len(parks_data['features'])} total)...")
                                renderer.add_national_parks(
                                    enabled_parks,
                                    stroke_color=parks_config.get("color", "#ff6b00"),
                                    fill_color=parks_config.get("fill", "none"),
                                    size=parks_config.get("size", 12),
                                    stroke_width=parks_config.get("stroke_width", 2)
                                )
                            else:
                                print("  No national parks enabled in configuration")
                        else:
                            print("  No national parks found in data file")
                    except FileNotFoundError:
                        progress_reporter.add_warning(f"National parks file not found: {parks_file}")
                    except Exception as e:
                        progress_reporter.add_warning(f"Failed to load national parks: {e}")
                else:
                    print("  National parks rendering disabled in configuration")
            
            # Add cities if enabled and we're in a USA region
            if args.region in ['usa', 'all']:
                cities_config = boundary_config.get("usa", {}).get("cities", {})
                if cities_config.get("enabled", False):
                    try:
                        cities_file = cities_config.get("data_file", "map_cache/us_cities.json")
                        print(f"  Loading cities from {cities_file}...")
                        
                        with open(cities_file, 'r') as f:
                            cities_data = json.load(f)
                        
                        # Get individual city settings
                        city_settings = config.get("us_cities", {})
                        
                        if cities_data.get("features"):
                            # Filter cities based on individual settings
                            enabled_cities = []
                            for city in cities_data["features"]:
                                city_name = city.get("properties", {}).get("name", "")
                                if city_settings.get(city_name, True):  # Default to True if not specified
                                    enabled_cities.append(city)
                            
                            if enabled_cities:
                                print(f"  Adding {len(enabled_cities)} cities (filtered from {len(cities_data['features'])} total)...")
                                renderer.add_cities(
                                    enabled_cities,
                                    stroke_color=cities_config.get("color", "#ff0000"),
                                    fill_color=cities_config.get("fill", "none"),
                                    size=cities_config.get("size", 16),
                                    stroke_width=cities_config.get("stroke_width", 2)
                                )
                            else:
                                print("  No cities enabled in configuration")
                        else:
                            print("  No cities found in data file")
                    except FileNotFoundError:
                        progress_reporter.add_warning(f"Cities file not found: {cities_file}")
                    except Exception as e:
                        progress_reporter.add_warning(f"Failed to load cities: {e}")
                else:
                    print("  Cities rendering disabled in configuration")
            
            # Add title and metadata
            athlete_name = f"{athlete_info['firstname']} {athlete_info['lastname']}"
            if args.region != 'all':
                region_title = args.region.replace('_', ' ').title()
                renderer.add_title(f"{athlete_name}'s Strava Activity Heatmap - {region_title}")
            else:
                renderer.add_title(f"{athlete_name}'s Strava Activity Heatmap")
            renderer.add_legend()
            
            # Save SVG with region-specific filename
            base_filename = output_config["filename"]
            if args.region != 'all':
                name_parts = base_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    output_file = f"{name_parts[0]}_{args.region}.{name_parts[1]}"
                else:
                    output_file = f"{base_filename}_{args.region}"
            else:
                output_file = base_filename
            
            renderer.save_svg(output_file)
            
            progress_reporter.log_file_operation("saved", output_file)
            
        except Exception as e:
            progress_reporter.add_error(f"Failed to create SVG: {e}")
            return
        
        # Show final summary
        bounds_info = calculate_gps_bounds(gps_data)
        additional_stats = {
            'Output file': output_file,
            'SVG dimensions': f"{output_config['width']} x {output_config['height']} pixels",
            'Geographic bounds': f"({bounds_info[0]:.3f}, {bounds_info[2]:.3f}) to ({bounds_info[1]:.3f}, {bounds_info[3]:.3f})",
            'Boundary paths included': sum(len(paths) for paths in boundary_data.values()),
            'Heatmap grid size': f"{grid_width} x {grid_height}"
        }
        
        progress_reporter.show_summary(additional_stats)
        print(f"\n🎉 Heatmap generation complete! SVG saved as: {output_file}")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt("Heatmap Generation")
    except Exception as e:
        print(f"❌ Heatmap generation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()