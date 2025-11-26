"""
Configuration for Rule-Based Grasp Detection System v3
Simple and easy to manage
"""

import torch

# ============================================================================
# Operating Modes
# ============================================================================

OPERATING_MODE = 'ROBOT'  # 'TESTING' or 'ROBOT'
CAPTURE_MODE = 'FRAME_BY_FRAME'  # 'REALTIME' or 'FRAME_BY_FRAME'

# ============================================================================
# Camera Settings
# ============================================================================

CAMERA_ID = 1
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# ============================================================================
# Object Detection (YOLOv8)
# ============================================================================

YOLO_MODEL = 'yolov8n'  # Fastest model
CONFIDENCE_THRESHOLD = 0.4  # Lower = detect more objects

# Optional: Filter specific classes
# None = detect all, or list of COCO class IDs
DETECT_CLASSES = None

# ============================================================================
# Depth Estimation (DepthAnything V2)
# ============================================================================

DEPTH_MODEL = 'vits'  # 'vits', 'vitb', 'vitl'
DEPTH_MODEL_PATH = 'Depth-Anything-V2/checkpoints/depth_anything_v2_vits.pth'

# ============================================================================
# Rule-Based Grasp Settings
# ============================================================================

# Minimum object size to consider (pixels)
MIN_OBJECT_WIDTH = 30
MIN_OBJECT_HEIGHT = 30

# Grasp orientations to try (degrees)
GRASP_ORIENTATIONS = [0, 45, 90, 135]  # horizontal, diagonal, vertical, diagonal

# Grasp dimensions
GRASP_LENGTH_RATIO = 0.6  # % of object dimension
GRASP_WIDTH = 40  # pixels

# Number of grasps to generate per object
MAX_GRASPS_PER_OBJECT = 4

# Quality scoring
DEPTH_VARIANCE_THRESHOLD = 0.1  # Lower = more uniform surface

# ============================================================================
# Visualization
# ============================================================================

SHOW_OBJECT_DETECTION = True
SHOW_DEPTH_MAP = True
SHOW_GRASPS = True

# Colors (BGR)
COLOR_BBOX = (0, 255, 0)      # Green
COLOR_GRASP = (255, 0, 0)     # Blue
COLOR_BEST_GRASP = (0, 0, 255)  # Red

# ============================================================================
# Results
# ============================================================================

SAVE_RESULTS = True
RESULTS_FOLDER = 'results'

# ============================================================================
# Robot Settings (Optional - for deployment)
# ============================================================================

# Workspace limits (mm) - ปรับตามการวัดจริงจาก Dobot MG400
# ใช้สำหรับป้องกันการเคลื่อนที่นอกขอบเขต
# ⚠️ ปรับค่าเหล่านี้ตามขอบเขตจริงของ workspace ของคุณ!
ROBOT_X_MIN = 150
ROBOT_X_MAX = 500
ROBOT_Y_MIN = -250
ROBOT_Y_MAX = 250
ROBOT_Z_MIN = -50
ROBOT_Z_MAX = 200


# ============================================================================
# Device
# ============================================================================

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

print(f"[Config] Mode: {OPERATING_MODE}, Capture: {CAPTURE_MODE}, Device: {DEVICE}")
