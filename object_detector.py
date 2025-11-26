"""
Object Detector - YOLOv8 wrapper
Copied from v2 and simplified
"""

import numpy as np
import cv2
from typing import List, Optional


class ObjectDetector:
    """YOLOv8 object detector"""
    
    def __init__(self, model_name='yolov8n', confidence_threshold=0.5, device='cpu'):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None
        
        # COCO class names
        self.class_names = self._get_coco_names()
    
    def load_model(self):
        """Load YOLOv8 model"""
        try:
            from ultralytics import YOLO
            print(f"Loading {self.model_name}...")
            
            self.model = YOLO(f'{self.model_name}.pt')
            
            if self.device == 'cuda':
                self.model.to('cuda')
            
            print(f"✓ Object detector loaded on {self.device}")
            return True
            
        except Exception as e:
            print(f"Error loading object detector: {e}")
            return False
    
    def detect(self, frame: np.ndarray, classes: Optional[List[int]] = None) -> List[dict]:
        """
        Detect objects in frame
        
        Args:
            frame: Input image (BGR)
            classes: Optional list of class IDs to detect
            
        Returns:
            List of detections with bbox, confidence, class_id, class_name
        """
        if self.model is None:
            return []
        
        # Run detection
        results = self.model(frame, conf=self.confidence_threshold, 
                           classes=classes, verbose=False)
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Extract box info
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                
                detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': conf,
                    'class_id': cls_id,
                    'class_name': self.class_names.get(cls_id, f'class_{cls_id}'),
                    'grasps': []  # Will be filled by grasp generator
                }
                
                detections.append(detection)
        
        return detections
    
    def _get_coco_names(self) -> dict:
        """COCO dataset class names"""
        return {
            0: 'person', 39: 'bottle', 40: 'wine glass', 41: 'cup', 
            42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl',
            46: 'banana', 47: 'apple', 56: 'chair', 57: 'couch',
            62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote',
            66: 'keyboard', 67: 'cell phone', 73: 'book', 
            74: 'clock', 75: 'vase', 76: 'scissors'
        }
