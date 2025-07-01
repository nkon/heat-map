import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Any
import math


class SVGRenderer:
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.svg_root = None
        self.projection = None
        
    def setup_projection(self, bounds: Tuple[float, float, float, float]):
        min_lat, min_lon, max_lat, max_lon = bounds
        
        # Simple equirectangular projection with aspect ratio correction
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        
        # Calculate scale to fit both dimensions
        lat_scale = self.height / lat_range
        lon_scale = self.width / lon_range
        
        # Use the smaller scale to ensure everything fits
        scale = min(lat_scale, lon_scale) * 0.9  # 90% to add some margin
        
        # Center the projection
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        self.projection = {
            'scale': scale,
            'center_lat': center_lat,
            'center_lon': center_lon,
            'offset_x': self.width / 2,
            'offset_y': self.height / 2
        }
    
    def lat_lon_to_svg(self, lat: float, lon: float) -> Tuple[float, float]:
        if not self.projection:
            raise ValueError("Projection not set up")
        
        proj = self.projection
        
        # Convert lat/lon to x/y coordinates
        x = (lon - proj['center_lon']) * proj['scale'] + proj['offset_x']
        y = (proj['center_lat'] - lat) * proj['scale'] + proj['offset_y']  # Flip Y axis
        
        return x, y
    
    def create_svg(self, bounds: Tuple[float, float, float, float]) -> ET.Element:
        self.setup_projection(bounds)
        
        self.svg_root = ET.Element('svg')
        self.svg_root.set('width', str(self.width))
        self.svg_root.set('height', str(self.height))
        self.svg_root.set('xmlns', 'http://www.w3.org/2000/svg')
        self.svg_root.set('viewBox', f'0 0 {self.width} {self.height}')
        
        # Add background
        background = ET.SubElement(self.svg_root, 'rect')
        background.set('width', '100%')
        background.set('height', '100%')
        background.set('fill', '#f8f9fa')
        
        return self.svg_root
    
    def add_boundary_paths(self, boundary_paths: List[List[Tuple[float, float]]], 
                          stroke_color: str = '#dee2e6', stroke_width: str = '0.5'):
        if not self.svg_root:
            raise ValueError("SVG not initialized")
        
        boundaries_group = ET.SubElement(self.svg_root, 'g')
        boundaries_group.set('id', 'boundaries')
        
        for path in boundary_paths:
            if len(path) < 2:
                continue
            
            svg_path = ET.SubElement(boundaries_group, 'path')
            
            path_data = []
            for i, (lat, lon) in enumerate(path):
                x, y = self.lat_lon_to_svg(lat, lon)
                if i == 0:
                    path_data.append(f'M {x:.2f} {y:.2f}')
                else:
                    path_data.append(f'L {x:.2f} {y:.2f}')
            
            # Close path if it's a polygon (first and last points are close)
            if len(path) > 2:
                first_point = path[0]
                last_point = path[-1]
                if (abs(first_point[0] - last_point[0]) < 0.001 and 
                    abs(first_point[1] - last_point[1]) < 0.001):
                    path_data.append('Z')
            
            svg_path.set('d', ' '.join(path_data))
            svg_path.set('stroke', stroke_color)
            svg_path.set('stroke-width', stroke_width)
            svg_path.set('fill', 'none')
    
    def add_heatmap_paths(self, heatmap_paths: List[List[Tuple[float, float]]], 
                         stroke_color: str = '#dc3545', stroke_width: str = '1.5'):
        if not self.svg_root:
            raise ValueError("SVG not initialized")
        
        heatmap_group = ET.SubElement(self.svg_root, 'g')
        heatmap_group.set('id', 'heatmap')
        
        for path in heatmap_paths:
            if len(path) < 2:
                continue
            
            svg_path = ET.SubElement(heatmap_group, 'path')
            
            path_data = []
            for i, (lat, lon) in enumerate(path):
                x, y = self.lat_lon_to_svg(lat, lon)
                if i == 0:
                    path_data.append(f'M {x:.2f} {y:.2f}')
                else:
                    path_data.append(f'L {x:.2f} {y:.2f}')
            
            svg_path.set('d', ' '.join(path_data))
            svg_path.set('stroke', stroke_color)
            svg_path.set('stroke-width', stroke_width)
            svg_path.set('fill', 'none')
            svg_path.set('stroke-linecap', 'round')
            svg_path.set('stroke-linejoin', 'round')
    
    def add_gps_tracks(self, gps_data: Dict[int, List[List[float]]], 
                      stroke_color: str = '#007bff', stroke_width: str = '1',
                      opacity: str = '0.6'):
        if not self.svg_root:
            raise ValueError("SVG not initialized")
        
        tracks_group = ET.SubElement(self.svg_root, 'g')
        tracks_group.set('id', 'gps-tracks')
        
        for activity_id, points in gps_data.items():
            if len(points) < 2:
                continue
            
            svg_path = ET.SubElement(tracks_group, 'path')
            
            path_data = []
            for i, point in enumerate(points):
                lat, lon = point[0], point[1]
                x, y = self.lat_lon_to_svg(lat, lon)
                if i == 0:
                    path_data.append(f'M {x:.2f} {y:.2f}')
                else:
                    path_data.append(f'L {x:.2f} {y:.2f}')
            
            svg_path.set('d', ' '.join(path_data))
            svg_path.set('stroke', stroke_color)
            svg_path.set('stroke-width', stroke_width)
            svg_path.set('fill', 'none')
            svg_path.set('opacity', opacity)
            svg_path.set('stroke-linecap', 'round')
            svg_path.set('stroke-linejoin', 'round')
    
    def add_title(self, title: str):
        if not self.svg_root:
            raise ValueError("SVG not initialized")
        
        title_text = ET.SubElement(self.svg_root, 'text')
        title_text.set('x', str(self.width / 2))
        title_text.set('y', '30')
        title_text.set('text-anchor', 'middle')
        title_text.set('font-family', 'Arial, sans-serif')
        title_text.set('font-size', '24')
        title_text.set('font-weight', 'bold')
        title_text.set('fill', '#333')
        title_text.text = title
    
    def add_legend(self):
        if not self.svg_root:
            raise ValueError("SVG not initialized")
        
        legend_group = ET.SubElement(self.svg_root, 'g')
        legend_group.set('id', 'legend')
        legend_group.set('transform', f'translate({self.width - 150}, {self.height - 80})')
        
        # Legend background
        legend_bg = ET.SubElement(legend_group, 'rect')
        legend_bg.set('width', '140')
        legend_bg.set('height', '70')
        legend_bg.set('fill', 'white')
        legend_bg.set('stroke', '#ccc')
        legend_bg.set('stroke-width', '1')
        legend_bg.set('rx', '5')
        
        # GPS tracks legend
        gps_line = ET.SubElement(legend_group, 'line')
        gps_line.set('x1', '10')
        gps_line.set('y1', '20')
        gps_line.set('x2', '30')
        gps_line.set('y2', '20')
        gps_line.set('stroke', '#007bff')
        gps_line.set('stroke-width', '2')
        
        gps_text = ET.SubElement(legend_group, 'text')
        gps_text.set('x', '35')
        gps_text.set('y', '25')
        gps_text.set('font-family', 'Arial, sans-serif')
        gps_text.set('font-size', '12')
        gps_text.set('fill', '#333')
        gps_text.text = 'GPS Tracks'
        
        # Boundaries legend
        boundary_line = ET.SubElement(legend_group, 'line')
        boundary_line.set('x1', '10')
        boundary_line.set('y1', '40')
        boundary_line.set('x2', '30')
        boundary_line.set('y2', '40')
        boundary_line.set('stroke', '#dee2e6')
        boundary_line.set('stroke-width', '1')
        
        boundary_text = ET.SubElement(legend_group, 'text')
        boundary_text.set('x', '35')
        boundary_text.set('y', '45')
        boundary_text.set('font-family', 'Arial, sans-serif')
        boundary_text.set('font-size', '12')
        boundary_text.set('fill', '#333')
        boundary_text.text = 'Boundaries'
    
    def save_svg(self, filename: str):
        if not self.svg_root:
            raise ValueError("SVG not initialized")
        
        # Create a rough indentation for readability
        self._indent(self.svg_root)
        
        tree = ET.ElementTree(self.svg_root)
        tree.write(filename, encoding='unicode', xml_declaration=True)
    
    def _indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i