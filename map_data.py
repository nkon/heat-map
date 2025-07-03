import requests
import json
from typing import List, Dict, Tuple, Any
import os


class MapDataProvider:
    def __init__(self, cache_dir: str = "map_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def get_world_boundaries(self) -> Dict[str, Any]:
        cache_file = os.path.join(self.cache_dir, "world_boundaries.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Use Natural Earth data for world boundaries
        url = "https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            return data
        except Exception as e:
            print(f"Failed to download world boundaries: {e}")
            return {"type": "FeatureCollection", "features": []}
    
    def get_us_states(self) -> Dict[str, Any]:
        cache_file = os.path.join(self.cache_dir, "us_states.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Use Natural Earth data for US states
        url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            return data
        except Exception as e:
            print(f"Failed to download US states: {e}")
            return {"type": "FeatureCollection", "features": []}

    def get_japan_prefectures(self) -> Dict[str, Any]:
        cache_file = os.path.join(self.cache_dir, "japan_prefectures.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Use Japan prefecture boundaries
        url = "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            return data
        except Exception as e:
            print(f"Failed to download Japan prefectures: {e}")
            return {"type": "FeatureCollection", "features": []}

    def get_minnesota_cities(self) -> Dict[str, Any]:
        cache_file = os.path.join(self.cache_dir, "minnesota_cities.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Use simple Minnesota city placeholders (Twin Cities area)
        # Create a basic set of major Minnesota cities as polygons
        print("    Creating Minnesota Twin Cities area boundaries...")
        
        # Major Twin Cities metro area cities with approximate boundaries
        cities = [
            {
                "type": "Feature",
                "properties": {"name": "Minneapolis"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-93.329, 44.901], [-93.329, 45.051], [-93.193, 45.051], 
                        [-93.193, 44.901], [-93.329, 44.901]
                    ]]
                }
            },
            {
                "type": "Feature", 
                "properties": {"name": "Saint Paul"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-93.193, 44.901], [-93.193, 44.975], [-93.063, 44.975],
                        [-93.063, 44.901], [-93.193, 44.901]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Bloomington"},
                "geometry": {
                    "type": "Polygon", 
                    "coordinates": [[
                        [-93.329, 44.831], [-93.329, 44.901], [-93.230, 44.901],
                        [-93.230, 44.831], [-93.329, 44.831]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Plymouth"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-93.455, 44.975], [-93.455, 45.051], [-93.329, 45.051],
                        [-93.329, 44.975], [-93.455, 44.975]
                    ]]
                }
            }
        ]
        
        data = {
            "type": "FeatureCollection",
            "features": cities
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        print(f"    Created {len(cities)} Twin Cities area boundaries")
        return data

    def get_lakes_data(self) -> Dict[str, Any]:
        cache_file = os.path.join(self.cache_dir, "lakes.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Use Natural Earth lakes data
        url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_lakes.geojson"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            return data
        except Exception as e:
            print(f"Failed to download lakes data: {e}")
            return {"type": "FeatureCollection", "features": []}
    
    def filter_boundaries_by_bounds(self, geojson_data: Dict[str, Any], 
                                  bounds: Tuple[float, float, float, float]) -> Dict[str, Any]:
        min_lat, min_lon, max_lat, max_lon = bounds
        filtered_features = []
        
        for feature in geojson_data.get("features", []):
            geometry = feature.get("geometry", {})
            if self._geometry_intersects_bounds(geometry, bounds):
                filtered_features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": filtered_features
        }
    
    def _geometry_intersects_bounds(self, geometry: Dict[str, Any], 
                                  bounds: Tuple[float, float, float, float]) -> bool:
        min_lat, min_lon, max_lat, max_lon = bounds
        
        def check_coordinates(coords):
            if isinstance(coords[0], (int, float)):
                lon, lat = coords[0], coords[1]
                return (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat)
            else:
                return any(check_coordinates(coord) for coord in coords)
        
        geom_type = geometry.get("type", "")
        coordinates = geometry.get("coordinates", [])
        
        if not coordinates:
            return False
        
        if geom_type in ["Point"]:
            return check_coordinates(coordinates)
        elif geom_type in ["LineString", "MultiPoint"]:
            return any(check_coordinates(coord) for coord in coordinates)
        elif geom_type in ["Polygon", "MultiLineString"]:
            return any(any(check_coordinates(coord) for coord in ring) for ring in coordinates)
        elif geom_type in ["MultiPolygon"]:
            return any(any(any(check_coordinates(coord) for coord in ring) for ring in polygon) 
                      for polygon in coordinates)
        
        return False
    
    def get_boundary_paths(self, geojson_data: Dict[str, Any]) -> List[List[Tuple[float, float]]]:
        paths = []
        
        for feature in geojson_data.get("features", []):
            geometry = feature.get("geometry", {})
            feature_paths = self._extract_paths_from_geometry(geometry)
            paths.extend(feature_paths)
        
        return paths
    
    def _extract_paths_from_geometry(self, geometry: Dict[str, Any]) -> List[List[Tuple[float, float]]]:
        paths = []
        geom_type = geometry.get("type", "")
        coordinates = geometry.get("coordinates", [])
        
        if geom_type == "LineString":
            path = [(coord[1], coord[0]) for coord in coordinates]  # Convert lon,lat to lat,lon
            paths.append(path)
        elif geom_type == "Polygon":
            for ring in coordinates:
                path = [(coord[1], coord[0]) for coord in ring]
                paths.append(path)
        elif geom_type == "MultiLineString":
            for line in coordinates:
                path = [(coord[1], coord[0]) for coord in line]
                paths.append(path)
        elif geom_type == "MultiPolygon":
            for polygon in coordinates:
                for ring in polygon:
                    path = [(coord[1], coord[0]) for coord in ring]
                    paths.append(path)
        
        return paths

    def is_japan_region(self, bounds: Tuple[float, float, float, float]) -> bool:
        """Check if bounds intersect with Japan"""
        min_lat, min_lon, max_lat, max_lon = bounds
        # Japan rough bounds: 24-46N, 123-146E
        japan_bounds = (24, 123, 46, 146)
        return self._bounds_intersect(bounds, japan_bounds)

    def is_usa_region(self, bounds: Tuple[float, float, float, float]) -> bool:
        """Check if bounds intersect with USA"""
        min_lat, min_lon, max_lat, max_lon = bounds
        # USA rough bounds: 24-72N, -180 to -66W
        usa_bounds = (24, -180, 72, -66)
        return self._bounds_intersect(bounds, usa_bounds)

    def is_minnesota_region(self, bounds: Tuple[float, float, float, float]) -> bool:
        """Check if bounds intersect with Minnesota"""
        min_lat, min_lon, max_lat, max_lon = bounds
        # Minnesota rough bounds: 43.5-49.4N, -97.2 to -89.5W
        mn_bounds = (43.5, -97.2, 49.4, -89.5)
        return self._bounds_intersect(bounds, mn_bounds)

    def _bounds_intersect(self, bounds1: Tuple[float, float, float, float], 
                         bounds2: Tuple[float, float, float, float]) -> bool:
        """Check if two bounding boxes intersect"""
        min_lat1, min_lon1, max_lat1, max_lon1 = bounds1
        min_lat2, min_lon2, max_lat2, max_lon2 = bounds2
        
        return not (max_lat1 < min_lat2 or min_lat1 > max_lat2 or 
                   max_lon1 < min_lon2 or min_lon1 > max_lon2)

    def get_detailed_boundaries(self, bounds: Tuple[float, float, float, float]) -> Dict[str, List[List[Tuple[float, float]]]]:
        """Get all relevant boundary data based on geographic region"""
        boundary_data = {}
        
        # World boundaries (load only if not in Japan/USA regions with detailed boundaries)
        load_world = not (self.is_japan_region(bounds) or self.is_usa_region(bounds))
        if load_world:
            print("  Loading world boundaries...")
            world_data = self.get_world_boundaries()
            filtered_world = self.filter_boundaries_by_bounds(world_data, bounds)
            boundary_data['world'] = self.get_boundary_paths(filtered_world)
        else:
            print("  Skipping world boundaries (loading detailed regional boundaries instead)...")
            boundary_data['world'] = []
        
        # Japan-specific boundaries
        if self.is_japan_region(bounds):
            print("  Loading Japan prefecture boundaries...")
            try:
                japan_data = self.get_japan_prefectures()
                filtered_japan = self.filter_boundaries_by_bounds(japan_data, bounds)
                boundary_data['japan_prefectures'] = self.get_boundary_paths(filtered_japan)
            except Exception as e:
                print(f"  Warning: Failed to load Japan boundaries: {e}")
                boundary_data['japan_prefectures'] = []
        
        # USA-specific boundaries
        if self.is_usa_region(bounds):
            print("  Loading US state boundaries...")
            try:
                us_data = self.get_us_states()
                filtered_us = self.filter_boundaries_by_bounds(us_data, bounds)
                boundary_data['us_states'] = self.get_boundary_paths(filtered_us)
            except Exception as e:
                print(f"  Warning: Failed to load US state boundaries: {e}")
                boundary_data['us_states'] = []
            
            # Minnesota cities if in Minnesota region
            if self.is_minnesota_region(bounds):
                print("  Loading Minnesota city boundaries...")
                try:
                    mn_data = self.get_minnesota_cities()
                    filtered_mn = self.filter_boundaries_by_bounds(mn_data, bounds)
                    boundary_data['minnesota_cities'] = self.get_boundary_paths(filtered_mn)
                except Exception as e:
                    print(f"  Warning: Failed to load Minnesota cities: {e}")
                    boundary_data['minnesota_cities'] = []
        
        # Lakes (for both Japan and USA)
        if self.is_japan_region(bounds) or self.is_usa_region(bounds):
            print("  Loading lakes and water bodies...")
            try:
                lakes_data = self.get_lakes_data()
                filtered_lakes = self.filter_boundaries_by_bounds(lakes_data, bounds)
                boundary_data['lakes'] = self.get_boundary_paths(filtered_lakes)
            except Exception as e:
                print(f"  Warning: Failed to load lakes data: {e}")
                boundary_data['lakes'] = []
        
        return boundary_data