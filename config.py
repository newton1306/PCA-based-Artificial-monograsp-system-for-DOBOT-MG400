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

# Workspace limits (mm) - ค่าทั้งหมดอ้างอิงจาก Online mode (Dobot Studio)
# ⚠️ ปรับค่าเหล่านี้ตามขอบเขตจริงของ workspace ของคุณ!
ROBOT_X_MIN = 150
ROBOT_X_MAX = 500
ROBOT_Y_MIN = -250
ROBOT_Y_MAX = 250
ROBOT_Z_MIN = -64  # ระยะต่ำสุดที่ gripper ลงได้ (ชิดพื้น)
ROBOT_Z_MAX = 200

# ความสูงสำหรับการจับวัตถุ (ค่า Online mode)
ROBOT_GRASP_HEIGHT = -62  # ความสูงที่ลงไปจับ (ชิดพื้น)
ROBOT_SAFE_HEIGHT = -30   # ความสูงปลอดภัย (ยกขึ้นมา)
ROBOT_DROP_POS = (250, 0, -30, 0)  # ตำแหน่งวางวัตถุ (X, Y, Z, R)

# Z Offset สำหรับ TCP/IP mode
# ============================================================================
# ปัญหา: ค่า Z ระหว่าง Online mode กับ TCP mode ไม่ตรงกัน
#   - Online mode (Dobot Studio): Z = -64 คือ gripper ชิดพื้น
#   - TCP mode: Z = -116 คือ gripper ชิดพื้น
# 
# สูตรการแปลง: TCP_Z = Online_Z - Offset
#   -116 = -64 - Offset  →  Offset = -64 - (-116) = 52
# ============================================================================
ROBOT_Z_OFFSET_TCP = 52  # Online → TCP: ลบค่านี้ออก

# ============================================================================
# ESP32 Gripper Settings
# ============================================================================

ESP32_PORT = 'COM9'        # Serial port for ESP32
ESP32_BAUDRATE = 115200    # Baud rate

# Servo angles (match esp32_gripper_control.ino)
GRIPPER_ANGLE_OPEN = 22    # กางแขนออกสุด
GRIPPER_ANGLE_CLOSE = 96   # หุบแขนเข้าสุด
GRIPPER_WIDTH_OPEN_MM = 74 # ความกว้าง gripper ที่มุม 22° (mm)

# Pick-and-Place Z heights
PICK_Z_SAFE = -50          # ความสูงปลอดภัย
PICK_Z_GRASP = -63         # ความสูงหยิบวัตถุ

# ============================================================================
# TF-Luna LiDAR Settings
# ============================================================================

# TF-Luna uses same ESP32 as Gripper (COM9)
# GPIO 16 (RX2) <- TF-Luna TX
# GPIO 17 (TX2) -> TF-Luna RX
LIDAR_GPIO_RX = 16
LIDAR_GPIO_TX = 17

# Z Reference: gripper closed, touching floor = Z_FLOOR
LIDAR_Z_FLOOR = -64        # Z เมื่อ gripper ติดพื้น (คีบสุด)

# Formula: Z_grasp = LIDAR_Z_FLOOR + object_height_mm


# ============================================================================
# Device
# ============================================================================

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

print(f"[Config] Mode: {OPERATING_MODE}, Capture: {CAPTURE_MODE}, Device: {DEVICE}")

