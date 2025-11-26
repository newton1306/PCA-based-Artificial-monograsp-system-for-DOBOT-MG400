"""
Simple Pipeline - Integrates object detection, depth estimation, and rule-based grasp
"""

import time
from typing import List, Dict
import numpy as np


class SimplePipeline:
    """Clean and simple grasp detection pipeline"""
    
    def __init__(self, config):
        self.config = config
        
        # Components (loaded separately)
        self.object_detector = None
        self.depth_estimator = None
        self.grasp_generator = None
        
        # Stats
        self.frame_count = 0
    
    def set_components(self, object_detector, depth_estimator, grasp_generator):
        """Set pipeline components"""
        self.object_detector = object_detector
        self.depth_estimator = depth_estimator
        self.grasp_generator = grasp_generator
    
    def process_frame(self, frame: np.ndarray, detect_objects: bool = True) -> Dict:
        """
        Process frame through complete pipeline
        
        Args:
            frame: Input frame (BGR)
            detect_objects: Whether to use object detection
            
        Returns:
            Dictionary with detections, depth_map, and timing info
        """
        result = {
            'detections': [],
            'depth_map': None,
            'timing': {}
        }
        
        # Step 1: Object Detection
        t_start = time.time()
        
        if detect_objects and self.object_detector:
            detections = self.object_detector.detect(
                frame, 
                classes=self.config.DETECT_CLASSES
            )
        else:
            # Process whole frame
            h, w = frame.shape[:2]
            detections = [{
                'bbox': [0, 0, w, h],
                'confidence': 1.0,
                'class_id': -1,
                'class_name': 'whole_frame',
                'grasps': []
            }]
        
        result['timing']['object_detection'] = time.time() - t_start
        result['detections'] = detections
        
        # Step 2: Depth Estimation
        t_start = time.time()
        
        if self.depth_estimator:
            depth_map = self.depth_estimator.estimate(frame)
            result['depth_map'] = depth_map
        else:
            # Fallback: zeros
            depth_map = np.zeros((frame.shape[0], frame.shape[1]))
            result['depth_map'] = depth_map
        
        result['timing']['depth_estimation'] = time.time() - t_start
        
        # Step 3: Generate Grasps
        t_start = time.time()
        
        if self.grasp_generator:
            for detection in detections:
                bbox = detection['bbox']
                
                # Generate grasps for this object
                grasps = self.grasp_generator.generate_grasps(
                    bbox, 
                    depth_map
                )
                
                detection['grasps'] = grasps
        
        result['timing']['grasp_generation'] = time.time() - t_start
        
        # Calculate total time
        result['timing']['total'] = sum(result['timing'].values())
        
        self.frame_count += 1
        
        return result
    
    def get_all_grasps(self, result: Dict) -> List:
        """Extract all grasps from result"""
        all_grasps = []
        
        for detection in result['detections']:
            all_grasps.extend(detection['grasps'])
        
        return all_grasps
    
    def get_best_grasp(self, result: Dict):
        """Get the best quality grasp across all objects"""
        all_grasps = self.get_all_grasps(result)
        
        if not all_grasps:
            return None
        
        return max(all_grasps, key=lambda g: g.quality)
    
    def get_stats(self) -> Dict:
        """Get pipeline statistics"""
        return {
            'frames_processed': self.frame_count
        }
