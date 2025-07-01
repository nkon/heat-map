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