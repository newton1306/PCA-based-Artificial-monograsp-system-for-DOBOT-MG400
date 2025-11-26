"""
Visualization utilities for rule-based grasp system
"""

import cv2
import numpy as np
from typing import List
import os
from datetime import datetime


def draw_bounding_boxes(image, detections, color=(0, 255, 0), thickness=2):
    """Draw bounding boxes on image"""
    img = image.copy()
    
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        
        # Draw box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        
        # Draw label
        label = f"{det['class_name']}: {det['confidence']:.2f}"
        
        # Text background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, y1 - th - 5), (x1 + tw, y1), color, -1)
        
        # Text
        cv2.putText(img, label, (x1, y1 - 2),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return img


def draw_grasps(image, grasps, best_grasp=None, 
                color=(255, 0, 0), best_color=(0, 0, 255), 
                thickness=2):
    """Draw grasp rectangles"""
    img = image.copy()
    
    for grasp in grasps:
        # Choose color
        if grasp is best_grasp:
            c = best_color
            t = thickness + 1
        else:
            c = color
            t = thickness
        
        # Get rectangle points
        points = grasp.get_rectangle_points()
        
        # Draw rectangle
        cv2.polylines(img, [points], isClosed=True, color=c, thickness=t)
        
        # Draw center
        cy, cx = grasp.center
        cv2.circle(img, (int(cx), int(cy)), 4, c, -1)
        
        # Draw quality score
        label = f"Q:{grasp.quality:.2f}"
        cv2.putText(img, label, (int(cx) + 8, int(cy) - 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1)
    
    return img


def create_depth_colormap(depth_map):
    """Create colored depth visualization"""
    # Normalize
    depth_norm = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min() + 1e-8)
    depth_uint8 = (depth_norm * 255).astype(np.uint8)
    
    # Apply colormap
    depth_colored = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_JET)
    
    return depth_colored


def create_side_by_side(images: List, labels: List = None):
    """Create side-by-side comparison"""
    if not images:
        return None
    
    # Ensure all images have same height
    target_height = images[0].shape[0]
    resized = []
    
    for img in images:
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        # Resize to same height
        aspect = img.shape[1] / img.shape[0]
        new_width = int(target_height * aspect)
        img_resized = cv2.resize(img, (new_width, target_height))
        
        # Add label if provided
        if labels:
            idx = len(resized)
            if idx < len(labels):
                img_resized = add_label(img_resized, labels[idx])
        
        resized.append(img_resized)
    
    # Concatenate
    combined = np.hstack(resized)
    
    return combined


def add_label(image, text, position='top'):
    """Add text label to image"""
    img = image.copy()
    h, w = img.shape[:2]
    
    # Text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.6
    thickness = 2
    
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    
    if position == 'top':
        y = th + 10
        rect_y1, rect_y2 = 0, th + 15
    else:  # bottom
        y = h - 10
        rect_y1, rect_y2 = h - th - 15, h
    
    # Background
    cv2.rectangle(img, (0, rect_y1), (w, rect_y2), (0, 0, 0), -1)
    
    # Text (centered)
    x = (w - tw) // 2
    cv2.putText(img, text, (x, y), font, scale, (255, 255, 255), thickness)
    
    return img


def add_info_text(image, info_dict, position='top-right'):
    """Add info panel"""
    img = image.copy()
    h, w = img.shape[:2]
    
    lines = [f"{k}: {v}" for k, v in info_dict.items()]
    
    # Calculate panel size
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1
    line_height = 20
    padding = 10
    
    max_width = max([cv2.getTextSize(line, font, scale, thickness)[0][0] 
                     for line in lines])
    
    panel_w = max_width + 2 * padding
    panel_h = len(lines) * line_height + 2 * padding
    
    # Position
    if position == 'top-right':
        x1 = w - panel_w - 10
        y1 = 10
    elif position == 'top-left':
        x1 = 10
        y1 = 10
    elif position == 'bottom-right':
        x1 = w - panel_w - 10
        y1 = h - panel_h - 10
    else:  # bottom-left
        x1 = 10
        y1 = h - panel_h - 10
    
    # Draw semi-transparent background
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x1 + panel_w, y1 + panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    
    # Draw text
    for i, line in enumerate(lines):
        y = y1 + padding + (i + 1) * line_height - 5
        cv2.putText(img, line, (x1 + padding, y), font, scale, (255, 255, 255), thickness)
    
    return img


def save_result(image, filename, folder='results'):
    """Save result image"""
    os.makedirs(folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(folder, f"{timestamp}_{filename}")
    
    cv2.imwrite(filepath, image)
    print(f"Saved: {filepath}")
    
    return filepath
