#!/usr/bin/env python3

"""
Strava Heatmap SVG Generator

Generates SVG heatmaps from Strava GPS data with geographic boundaries.
Refactored to use centralized utilities for configuration, file operations,
progress reporting, and data validation.
"""

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
    calculate_heatmap_resolution
)


def main():
    """Main heatmap generation process"""
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
            
        except Exception as e:
            progress_reporter.add_error(f"Failed to generate heatmap: {e}")
            return
        
        # Load map boundaries
        print("\n🗺️  Loading geographic boundaries...")
        try:
            map_provider = MapDataProvider()
            world_paths = []
            
            # Get world boundaries
            print("  Loading world boundaries...")
            world_data = map_provider.get_world_boundaries()
            filtered_world = map_provider.filter_boundaries_by_bounds(world_data, bounds)
            world_paths = map_provider.get_boundary_paths(filtered_world)
            
            # Get US states if in US bounds
            us_bounds = (24, -125, 50, -66)  # Rough US bounds
            min_lat, max_lat, min_lon, max_lon = bounds
            if (min_lat >= us_bounds[0] and min_lon >= us_bounds[1] and 
                max_lat <= us_bounds[2] and max_lon <= us_bounds[3]):
                print("  Loading US state boundaries...")
                us_data = map_provider.get_us_states()
                filtered_us = map_provider.filter_boundaries_by_bounds(us_data, bounds)
                us_paths = map_provider.get_boundary_paths(filtered_us)
                world_paths.extend(us_paths)
            
            progress_reporter.log_file_operation(
                "loaded", 
                f"geographic boundaries ({len(world_paths)} paths)"
            )
            
        except Exception as e:
            progress_reporter.add_warning(f"Failed to load map boundaries: {e}")
            progress_reporter.add_warning("Continuing without geographic boundaries")
            world_paths = []
        
        # Create SVG
        print("\n🎨 Creating SVG visualization...")
        try:
            style_config = config["style"]
            
            renderer = SVGRenderer(
                width=output_config["width"],
                height=output_config["height"]
            )
            
            # Create SVG with bounds
            renderer.create_svg(bounds)
            
            # Add boundaries first (so tracks appear on top)
            if world_paths:
                print(f"  Adding {len(world_paths)} boundary paths...")
                renderer.add_boundary_paths(
                    world_paths,
                    stroke_color=style_config["boundary_color"],
                    stroke_width=style_config["boundary_width"]
                )
            
            # Add GPS tracks
            print(f"  Adding GPS tracks from {len(gps_data)} activities...")
            renderer.add_gps_tracks(
                gps_data,
                stroke_color=style_config["track_color"],
                stroke_width=style_config["track_width"]
            )
            
            # Add title and metadata
            athlete_name = f"{athlete_info['firstname']} {athlete_info['lastname']}"
            renderer.add_title(f"{athlete_name}'s Strava Activity Heatmap")
            renderer.add_legend()
            
            # Save SVG
            output_file = output_config["filename"]
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
            'Boundary paths included': len(world_paths),
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