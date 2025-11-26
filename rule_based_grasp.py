"""
Rule-Based Grasp Generator
Calculates grasp points using geometric rules instead of ML models
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict


class Grasp:
    """Simple grasp representation"""
    
    def __init__(self, center, angle, length, width, quality=0.0):
        """
        Args:
            center: (y, x) center point
            angle: Grasp angle in radians
            length: Grasp length in pixels
            width: Grasp width in pixels
            quality: Quality score (0-1)
        """
        self.center = center
        self.angle = angle
        self.length = length
        self.width = width
        self.quality = quality
    
    def get_rectangle_points(self):
        """
        Get the 4 corner points of grasp rectangle
        
        Returns:
            numpy array of shape (4, 2) with corner points
        """
        cy, cx = self.center
        
        # Calculate unit vectors
        cos_a = np.cos(self.angle)
        sin_a = np.sin(self.angle)
        
        # Half dimensions
        hl = self.length / 2
        hw = self.width / 2
        
        # Corner points (relative to center)
        corners = np.array([
            [-hl, -hw],
            [-hl, +hw],
            [+hl, +hw],
            [+hl, -hw]
        ])
        
        # Rotation matrix
        R = np.array([
            [cos_a, -sin_a],
            [sin_a, cos_a]
        ])
        
        # Rotate and translate
        rotated = corners @ R.T
        points = rotated + np.array([cy, cx])
        
        # Return as (x, y) for OpenCV
        return points[:, [1, 0]].astype(int)
    
    def __repr__(self):
        return f"Grasp(center={self.center}, angle={np.degrees(self.angle):.1f}°, quality={self.quality:.3f})"


class RuleBasedGraspGenerator:
    """Generate grasps using geometric rules"""
    
    def __init__(self, config):
        self.config = config
    
    def generate_grasps(self, bbox: Tuple[int, int, int, int], 
                       depth_map: np.ndarray,
                       orientations: List[float] = None) -> List[Grasp]:
        """
        Generate grasps for an object bounding box
        
        Args:
            bbox: (x1, y1, x2, y2) bounding box
            depth_map: Depth map of the scene
            orientations: List of angles in degrees
            
        Returns:
            List of Grasp objects sorted by quality
        """
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        
        # Check minimum size
        if w < self.config.MIN_OBJECT_WIDTH or h < self.config.MIN_OBJECT_HEIGHT:
            return []
        
        # Calculate center
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        # Use configured orientations if not specified
        if orientations is None:
            orientations = self.config.GRASP_ORIENTATIONS
        
        grasps = []
        
        for angle_deg in orientations:
            angle_rad = np.radians(angle_deg)
            
            # Calculate grasp length based on orientation
            if angle_deg % 180 == 0:  # Horizontal
                grasp_length = int(w * self.config.GRASP_LENGTH_RATIO)
            elif angle_deg % 180 == 90:  # Vertical
                grasp_length = int(h * self.config.GRASP_LENGTH_RATIO)
            else:  # Diagonal
                grasp_length = int(np.sqrt(w**2 + h**2) * self.config.GRASP_LENGTH_RATIO * 0.7)
            
            # Create grasp
            grasp = Grasp(
                center=(cy, cx),
                angle=angle_rad,
                length=grasp_length,
                width=self.config.GRASP_WIDTH
            )
            
            # Calculate quality score
            quality = self._score_grasp(grasp, bbox, depth_map)
            grasp.quality = quality
            
            # Validate grasp is within bounds
            if self._validate_grasp(grasp, bbox):
                grasps.append(grasp)
        
        # Sort by quality (highest first)
        grasps.sort(key=lambda g: g.quality, reverse=True)
        
        # Return top N grasps
        return grasps[:self.config.MAX_GRASPS_PER_OBJECT]
    
    def _score_grasp(self, grasp: Grasp, bbox: Tuple[int, int, int, int], 
                     depth_map: np.ndarray) -> float:
        """
        Score grasp quality based on depth variance
        
        Lower depth variance = more uniform surface = better grasp
        
        Args:
            grasp: Grasp object
            bbox: Bounding box
            depth_map: Depth map
            
        Returns:
            Quality score (0-1, higher is better)
        """
        x1, y1, x2, y2 = bbox
        cy, cx = grasp.center
        
        # Extract depth ROI along grasp line
        try:
            # Sample points along grasp length
            num_samples = 10
            cos_a = np.cos(grasp.angle)
            sin_a = np.sin(grasp.angle)
            
            depth_samples = []
            
            for i in range(num_samples):
                t = (i / (num_samples - 1) - 0.5) * grasp.length
                sample_y = int(cy + t * sin_a)
                sample_x = int(cx + t * cos_a)
                
                # Check bounds
                if y1 <= sample_y < y2 and x1 <= sample_x < x2:
                    depth_val = depth_map[sample_y, sample_x]
                    depth_samples.append(depth_val)
            
            if len(depth_samples) < 3:
                return 0.0
            
            # Calculate variance
            depth_variance = np.var(depth_samples)
            
            # Convert to quality score (lower variance = higher quality)
            # Use exponential decay
            quality = np.exp(-depth_variance / self.config.DEPTH_VARIANCE_THRESHOLD)
            
            # Normalize to 0-1
            quality = np.clip(quality, 0.0, 1.0)
            
            return float(quality)
            
        except:
            return 0.0
    
    def _validate_grasp(self, grasp: Grasp, bbox: Tuple[int, int, int, int]) -> bool:
        """
        Validate that grasp is within bounding box
        
        Args:
            grasp: Grasp object
            bbox: Bounding box
            
        Returns:
            True if valid
        """
        x1, y1, x2, y2 = bbox
        cy, cx = grasp.center
        
        # Check center is within bbox (with small margin)
        margin = 5
        if not (x1 + margin <= cx <= x2 - margin and 
                y1 + margin <= cy <= y2 - margin):
            return False
        
        # Check grasp endpoints are reasonably within bbox
        cos_a = np.cos(grasp.angle)
        sin_a = np.sin(grasp.angle)
        
        hl = grasp.length / 2
        
        # Check both endpoints
        for sign in [-1, 1]:
            end_y = cy + sign * hl * sin_a
            end_x = cx + sign * hl * cos_a
            
            # Allow some tolerance
            tolerance = 10
            if not (x1 - tolerance <= end_x <= x2 + tolerance and 
                    y1 - tolerance <= end_y <= y2 + tolerance):
                return False
        
        return True
    
    def get_best_grasp(self, grasps: List[Grasp]) -> Grasp:
        """Get the best quality grasp"""
        if not grasps:
            return None
        return max(grasps, key=lambda g: g.quality)
