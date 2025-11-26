"""
Depth Estimator - Wrapper for DepthAnything V2
"""

import sys
import torch
import numpy as np

sys.path.append('Depth-Anything-V2')
from depth_anything_v2.dpt import DepthAnythingV2


class DepthEstimator:
    """Simple wrapper for depth estimation"""
    
    def __init__(self, model_name='vits', model_path=None, device='cpu'):
        """
        Initialize depth estimator
        
        Args:
            model_name: 'vits', 'vitb', or 'vitl'
            model_path: Path to model checkpoint
            device: 'cpu' or 'cuda'
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        
        # Model configurations
        self.configs = {
            'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
            'vitb': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
            'vitl': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]}
        }
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path):
        """Load depth estimation model"""
        print(f"Loading DepthAnything V2 ({self.model_name})...")
        
        try:
            config = self.configs[self.model_name]
            self.model = DepthAnythingV2(**config)
            
            # Load weights
            state_dict = torch.load(model_path, map_location='cpu')
            self.model.load_state_dict(state_dict)
            
            # Move to device and set to eval mode
            self.model = self.model.to(self.device).eval()
            
            print(f"✓ Depth model loaded on {self.device}")
            return True
            
        except Exception as e:
            print(f"Error loading depth model: {e}")
            return False
    
    def estimate(self, frame):
        """
        Estimate depth from frame
        
        Args:
            frame: Input image (BGR, numpy array)
            
        Returns:
            Depth map (numpy array, same size as input)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Infer depth
        depth = self.model.infer_image(frame)
        
        return depth
    
    def estimate_normalized(self, frame):
        """
        Estimate depth and normalize to 0-1 range
        
        Args:
            frame: Input image
            
        Returns:
            Normalized depth map (0-1 range)
        """
        depth = self.estimate(frame)
        
        # Normalize to 0-1
        depth_min = depth.min()
        depth_max = depth.max()
        
        if depth_max > depth_min:
            depth_norm = (depth - depth_min) / (depth_max - depth_min)
        else:
            depth_norm = np.zeros_like(depth)
        
        return depth_norm
    
    def get_depth_at_point(self, depth_map, x, y):
        """
        Get depth value at specific point
        
        Args:
            depth_map: Depth map
            x, y: Pixel coordinates
            
        Returns:
            Depth value at (x, y)
        """
        h, w = depth_map.shape
        
        # Clamp coordinates
        x = max(0, min(w - 1, int(x)))
        y = max(0, min(h - 1, int(y)))
        
        return depth_map[y, x]
    
    def get_depth_stats(self, depth_map, x1, y1, x2, y2):
        """
        Get depth statistics in a region
        
        Args:
            depth_map: Depth map
            x1, y1, x2, y2: Region bounds
            
        Returns:
            Dictionary with mean, std, min, max
        """
        # Extract region
        roi = depth_map[y1:y2, x1:x2]
        
        stats = {
            'mean': np.mean(roi),
            'std': np.std(roi),
            'min': np.min(roi),
            'max': np.max(roi),
            'variance': np.var(roi)
        }
        
        return stats
