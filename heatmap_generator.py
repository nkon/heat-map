import numpy as np
from typing import List, Tuple, Dict, Any
import math
from collections import defaultdict


class HeatmapGenerator:
    def __init__(self, bounds: Tuple[float, float, float, float] = None, resolution: int = 1000):
        self.bounds = bounds  # (min_lat, min_lon, max_lat, max_lon)
        self.resolution = resolution
        self.grid = None
        self.lat_scale = None
        self.lon_scale = None
        
    def _calculate_bounds(self, gps_data: Dict[int, List[List[float]]]) -> Tuple[float, float, float, float]:
        all_points = []
        for activity_points in gps_data.values():
            all_points.extend(activity_points)
        
        if not all_points:
            return (0, 0, 0, 0)
        
        lats = [point[0] for point in all_points]
        lons = [point[1] for point in all_points]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Add small margin
        lat_margin = (max_lat - min_lat) * 0.05
        lon_margin = (max_lon - min_lon) * 0.05
        
        return (min_lat - lat_margin, min_lon - lon_margin, 
                max_lat + lat_margin, max_lon + lon_margin)
    
    def _setup_grid(self, bounds: Tuple[float, float, float, float]):
        self.bounds = bounds
        min_lat, min_lon, max_lat, max_lon = bounds
        
        self.lat_scale = self.resolution / (max_lat - min_lat)
        self.lon_scale = self.resolution / (max_lon - min_lon)
        self.grid = np.zeros((self.resolution, self.resolution))
    
    def _lat_lon_to_grid(self, lat: float, lon: float) -> Tuple[int, int]:
        min_lat, min_lon, _, _ = self.bounds
        
        grid_lat = int((lat - min_lat) * self.lat_scale)
        grid_lon = int((lon - min_lon) * self.lon_scale)
        
        grid_lat = max(0, min(self.resolution - 1, grid_lat))
        grid_lon = max(0, min(self.resolution - 1, grid_lon))
        
        return grid_lat, grid_lon
    
    def _grid_to_lat_lon(self, grid_lat: int, grid_lon: int) -> Tuple[float, float]:
        min_lat, min_lon, _, _ = self.bounds
        
        lat = min_lat + grid_lat / self.lat_scale
        lon = min_lon + grid_lon / self.lon_scale
        
        return lat, lon
    
    def _add_line_to_grid(self, start_point: List[float], end_point: List[float]):
        start_lat, start_lon = start_point
        end_lat, end_lon = end_point
        
        start_grid = self._lat_lon_to_grid(start_lat, start_lon)
        end_grid = self._lat_lon_to_grid(end_lat, end_lon)
        
        # Bresenham's line algorithm adaptation for drawing lines on grid
        x0, y0 = start_grid
        x1, y1 = end_grid
        
        points = self._bresenham_line(x0, y0, x1, y1)
        
        for x, y in points:
            if 0 <= x < self.resolution and 0 <= y < self.resolution:
                self.grid[x, y] = 1
    
    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        
        dx *= 2
        dy *= 2
        
        for _ in range(n):
            points.append((x, y))
            
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx
                
        return points
    
    def generate_heatmap(self, gps_data: Dict[int, List[List[float]]]) -> np.ndarray:
        if self.bounds is None:
            self.bounds = self._calculate_bounds(gps_data)
        
        self._setup_grid(self.bounds)
        
        for activity_id, activity_points in gps_data.items():
            if len(activity_points) < 2:
                continue
                
            for i in range(len(activity_points) - 1):
                self._add_line_to_grid(activity_points[i], activity_points[i + 1])
        
        return self.grid
    
    def get_heatmap_paths(self) -> List[List[Tuple[float, float]]]:
        if self.grid is None:
            return []
        
        paths = []
        visited = np.zeros_like(self.grid, dtype=bool)
        
        for i in range(self.resolution):
            for j in range(self.resolution):
                if self.grid[i, j] > 0 and not visited[i, j]:
                    path = self._trace_path(i, j, visited)
                    if len(path) > 1:
                        # Convert grid coordinates to lat/lon
                        lat_lon_path = [self._grid_to_lat_lon(x, y) for x, y in path]
                        paths.append(lat_lon_path)
        
        return paths
    
    def _trace_path(self, start_i: int, start_j: int, visited: np.ndarray) -> List[Tuple[int, int]]:
        path = []
        stack = [(start_i, start_j)]
        
        while stack:
            i, j = stack.pop()
            if visited[i, j] or self.grid[i, j] == 0:
                continue
                
            visited[i, j] = True
            path.append((i, j))
            
            # Check 8-connected neighbors
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if (0 <= ni < self.resolution and 0 <= nj < self.resolution and
                        not visited[ni, nj] and self.grid[ni, nj] > 0):
                        stack.append((ni, nj))
        
        return path
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        return self.bounds if self.bounds else (0, 0, 0, 0)