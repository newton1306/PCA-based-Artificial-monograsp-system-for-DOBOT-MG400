# 🤖 Auto-Pick System v15
# Auto-detect objects, wait for stability, countdown, then pick automatically

import cv2
import numpy as np
import time
import socket
import serial
from enum import Enum

print("✓ Imports (v15)")

# ============================================================
# HARDWARE CONFIGURATION
# ============================================================
ROBOT_IP = '192.168.1.6'
ESP32_PORT = 'COM9'
ESP32_BAUDRATE = 115200
CAMERA_ID = 2
HOMOGRAPHY_MATRIX = np.load('homography_matrix.npy')
print("✓ Hardware config")

# ============================================================
# CONFIGURATION v15
# ============================================================
PIXELS_PER_MM = 2.7703
ROBOT_R_OFFSET = -25.55
Z_FLOOR = -64
Z_MEASURE = 120
LIDAR_PHYSICAL_OFFSET = 60
LIDAR_CORRECTION = -21
LIDAR_X_OFFSET = 25.08
LIDAR_Y_OFFSET = 20.71
HEIGHT_CORRECTION_FACTOR = 0.115
DROP_POS = (169.71, 58.01, -17.07, 13.78)
GRIPPER_MAX_WIDTH_MM = 54
GRIPPER_OPEN_MARGIN_MM = 5
GRIPPER_GRIP_MARGIN_MM = 5
MIN_OBJECT_AREA = 800
MAX_OBJECT_AREA = 50000
DONUT_HOLE_RATIO_MIN = 0.1
DONUT_HOLE_RATIO_MAX = 0.7
DONUT_CIRCULARITY_MIN = 0.5

# v15 AUTO-PICK PARAMETERS
AUTO_STABLE_TIME_SEC = 4.0      # วัตถุต้องนิ่งกี่วินาที
AUTO_COUNTDOWN_SEC = 3.0        # นับถอยหลังกี่วินาที
AUTO_POSITION_TOLERANCE = 20    # พิกเซล tolerance
AUTO_AREA_TOLERANCE = 0.15      # 15% area tolerance
AUTO_COOLDOWN_SEC = 3.0         # cooldown หลังหยิบ
AUTO_MODE_ENABLED = True        # เปิด/ปิด auto mode

print("✓ Configuration v15")

# ============================================================
# STATE MACHINE
# ============================================================
class AutoState(Enum):
    IDLE = "idle"
    DETECTED = "detected"
    STABLE = "stable"
    COUNTDOWN = "countdown"
    PICKING = "picking"
    COOLDOWN = "cooldown"

STATE_COLORS = {
    AutoState.IDLE: (100, 100, 100),
    AutoState.DETECTED: (0, 200, 255),
    AutoState.STABLE: (255, 200, 0),
    AutoState.COUNTDOWN: (0, 128, 255),
    AutoState.PICKING: (0, 0, 255),
    AutoState.COOLDOWN: (128, 128, 128),
}

STATE_MESSAGES = {
    AutoState.IDLE: "🔍 Scanning for objects...",
    AutoState.DETECTED: "👀 Object detected!",
    AutoState.STABLE: "✋ Hold still...",
    AutoState.COUNTDOWN: "⏱️ Countdown...",
    AutoState.PICKING: "🤖 Picking...",
    AutoState.COOLDOWN: "⏸️ Cooldown...",
}

class AutoPickStateMachine:
    def __init__(self):
        self.state = AutoState.IDLE
        self.tracked_center = None
        self.tracked_area = None
        self.tracked_object = None
        self.selected_grasp = None
        self.detect_time = None
        self.stable_time = None
        self.countdown_time = None
        self.cooldown_time = None
    
    def reset(self):
        self.state = AutoState.IDLE
        self.tracked_center = None
        self.tracked_area = None
        self.tracked_object = None
        self.selected_grasp = None
        self.detect_time = None
        self.stable_time = None
        self.countdown_time = None
    
    def find_closest_to_center(self, objects, frame_center):
        if not objects:
            return None
        min_dist = float('inf')
        closest = None
        for obj in objects:
            cx, cy = obj['center']
            dist = np.sqrt((cx - frame_center[0])**2 + (cy - frame_center[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest = obj
        return closest
    
    def is_same_object(self, obj):
        if self.tracked_center is None:
            return False
        cx, cy = obj['center']
        dx = abs(cx - self.tracked_center[0])
        dy = abs(cy - self.tracked_center[1])
        area_diff = abs(obj['area'] - self.tracked_area) / max(self.tracked_area, 1)
        return dx < AUTO_POSITION_TOLERANCE and dy < AUTO_POSITION_TOLERANCE and area_diff < AUTO_AREA_TOLERANCE
    
    def update(self, objects, grasp_selector, frame_center):
        now = time.time()
        
        if self.state == AutoState.COOLDOWN:
            if now - self.cooldown_time >= AUTO_COOLDOWN_SEC:
                self.reset()
            return None
        
        if self.state == AutoState.PICKING:
            return None
        
        target = self.find_closest_to_center(objects, frame_center)
        
        if target is None:
            if self.state != AutoState.IDLE:
                self.reset()
            return None
        
        if self.state == AutoState.IDLE:
            self.state = AutoState.DETECTED
            self.tracked_center = target['center']
            self.tracked_area = target['area']
            self.tracked_object = target
            self.detect_time = now
            grasps = grasp_selector.analyze_object(target)
            self.selected_grasp = grasps[0] if grasps else None
            return None
        
        if not self.is_same_object(target):
            self.state = AutoState.DETECTED
            self.tracked_center = target['center']
            self.tracked_area = target['area']
            self.tracked_object = target
            self.detect_time = now
            self.stable_time = None
            self.countdown_time = None
            grasps = grasp_selector.analyze_object(target)
            self.selected_grasp = grasps[0] if grasps else None
            return None
        
        self.tracked_center = target['center']
        self.tracked_area = target['area']
        self.tracked_object = target
        
        if self.state == AutoState.DETECTED:
            if now - self.detect_time >= AUTO_STABLE_TIME_SEC:
                self.state = AutoState.STABLE
                self.stable_time = now
            return None
        
        if self.state == AutoState.STABLE:
            self.state = AutoState.COUNTDOWN
            self.countdown_time = now
            return None
        
        if self.state == AutoState.COUNTDOWN:
            remaining = AUTO_COUNTDOWN_SEC - (now - self.countdown_time)
            if remaining <= 0:
                self.state = AutoState.PICKING
                return "PICK"
            return None
        
        return None
    
    def get_countdown_remaining(self):
        if self.state != AutoState.COUNTDOWN or self.countdown_time is None:
            return 0
        return max(0, AUTO_COUNTDOWN_SEC - (time.time() - self.countdown_time))
    
    def get_stable_progress(self):
        if self.state == AutoState.DETECTED and self.detect_time:
            return min(1.0, (time.time() - self.detect_time) / AUTO_STABLE_TIME_SEC)
        return 0
    
    def start_cooldown(self):
        self.state = AutoState.COOLDOWN
        self.cooldown_time = time.time()
        self.tracked_object = None
        self.selected_grasp = None

print("✓ AutoPickStateMachine")

# ============================================================
# SMART GRIPPER CONTROLLER
# ============================================================
class SmartGripperController:
    CALIB_ANGLES = np.array([22, 30, 40, 50, 60, 70, 80, 90, 96])
    CALIB_WIDTHS = np.array([54.0, 52.0, 48.0, 40.0, 32.0, 23.0, 12.0, 3.0, 0.0])
    
    def __init__(self, port='COM9', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.target_width = None
        
    def connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)
            self.serial.reset_input_buffer()
            print(f"✅ Gripper+LIDAR on {self.port}")
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False
    
    def disconnect(self):
        if self.serial: 
            self.serial.close()
            self.serial = None
    
    def send_command(self, cmd):
        if self.serial and self.serial.is_open:
            self.serial.reset_input_buffer()
            self.serial.write((cmd + '\n').encode())
            time.sleep(0.3)
    
    def mm_to_angle(self, width_mm):
        width = max(0.0, min(54.0, width_mm))
        return int(round(np.interp(width, self.CALIB_WIDTHS[::-1], self.CALIB_ANGLES[::-1])))
    
    def open_for_object(self, width_mm):
        self.target_width = width_mm
        open_w = min(54.0, width_mm + GRIPPER_OPEN_MARGIN_MM)
        angle = self.mm_to_angle(open_w)
        print(f"🦾 Open: {open_w:.1f}mm ({angle}°)")
        self.send_command(f'G{angle}')
    
    def open_to_width(self, width_mm):
        self.target_width = width_mm
        angle = self.mm_to_angle(width_mm)
        print(f"🦾 Pre-open: {width_mm:.1f}mm ({angle}°)")
        self.send_command(f'G{angle}')
    
    def grip_object(self, width_mm):
        grip_w = max(0.0, width_mm - GRIPPER_GRIP_MARGIN_MM)
        angle = self.mm_to_angle(grip_w)
        print(f"🦾 Grip: {grip_w:.1f}mm ({angle}°)")
        self.send_command(f'G{angle}')
    
    def release(self):
        open_w = min(54.0, (self.target_width or 30) + 10)
        self.send_command(f'G{self.mm_to_angle(open_w)}')
        self.target_width = None
    
    def read_lidar(self, samples=5):
        if not self.serial or not self.serial.is_open:
            return None
        readings = []
        for _ in range(samples):
            self.serial.reset_input_buffer()
            self.serial.write(b'L\n')
            start = time.time()
            while time.time() - start < 1.0:
                if self.serial.in_waiting > 0:
                    response = self.serial.readline().decode().strip()
                    if response.startswith("LIDAR:") and "ERR" not in response:
                        try:
                            readings.append(int(response.split(":")[1]))
                        except:
                            pass
                        break
            time.sleep(0.05)
        return int(np.median(readings)) if readings else None

print("✓ SmartGripperController")

# ============================================================
# DOBOT CONTROLLER TCP
# ============================================================
class DobotControllerTCP:
    def __init__(self, homography_matrix=None, r_offset=-25.55):
        self.dashboard_port = 29999
        self.sock = None
        self.H = homography_matrix
        self.r_offset = r_offset
        
    def connect(self, ip):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((ip, self.dashboard_port))
            self.send_command("ClearError()")
            time.sleep(0.5)
            self.send_command("EnableRobot()")
            time.sleep(4)
            self.send_command("User(1)")
            self.send_command("Tool(1)")
            self.send_command("SpeedFactor(50)")
            print("✅ Robot connected!")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def send_command(self, cmd):
        if self.sock:
            self.sock.send((cmd + "\n").encode("utf-8"))
            return self.sock.recv(1024).decode("utf-8")

    def home(self):
        print("🤖 HOME...")
        self.send_command("MovJ(-253.07, 115.17, -17.07, -62.78)")
        time.sleep(4)

    def move_to(self, x, y, z, r=0):
        cmd = f"MovJ({x},{y},{z},{r})"
        print(f"   → {cmd}")
        return self.send_command(cmd)
    
    def move_to_and_wait(self, x, y, z, r=0, wait=3):
        self.move_to(x, y, z, r)
        time.sleep(wait)
    
    def joint_move(self, j1=0, j2=0, j3=0, j4=0):
        cmd = f"JointMovJ({j1},{j2},{j3},{j4})"
        print(f"   → {cmd}")
        return self.send_command(cmd)
    
    def joint_move_and_wait(self, j1=0, j2=0, j3=0, j4=0, wait=3):
        self.joint_move(j1, j2, j3, j4)
        time.sleep(wait)

    def pixel_to_robot(self, u, v):
        if self.H is None: return None, None
        pt = np.array([u, v, 1], dtype=np.float32)
        res = np.dot(self.H, pt)
        return res[0]/res[2], res[1]/res[2]
    
    def camera_angle_to_robot_r(self, camera_angle):
        return self.r_offset - camera_angle

print("✓ DobotControllerTCP")

# ============================================================
# OBJECT DETECTOR V15
# ============================================================
class ObjectDetectorV15:
    def __init__(self, pixels_per_mm):
        self.ppm = pixels_per_mm
    
    def detect(self, frame):
        objects = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        _, sat_mask = cv2.threshold(s, 50, 255, cv2.THRESH_BINARY)
        _, dark_mask = cv2.threshold(v, 80, 255, cv2.THRESH_BINARY_INV)
        combined_mask = cv2.bitwise_or(sat_mask, dark_mask)
        kernel = np.ones((5, 5), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        
        contours, hierarchy = cv2.findContours(combined_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None:
            return objects
        hierarchy = hierarchy[0]
        
        for i, cnt in enumerate(contours):
            if hierarchy[i][3] != -1:
                continue
            area = cv2.contourArea(cnt)
            if not (MIN_OBJECT_AREA < area < MAX_OBJECT_AREA):
                continue
            
            hole_area = 0
            hole_contour = None
            child_idx = hierarchy[i][2]
            while child_idx != -1:
                child_area = cv2.contourArea(contours[child_idx])
                if child_area > hole_area:
                    hole_area = child_area
                    hole_contour = contours[child_idx]
                child_idx = hierarchy[child_idx][0]
            
            hole_ratio = hole_area / area if area > 0 else 0
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            is_donut = (DONUT_HOLE_RATIO_MIN <= hole_ratio <= DONUT_HOLE_RATIO_MAX and circularity >= DONUT_CIRCULARITY_MIN)
            
            hull = cv2.convexHull(cnt)
            rect = cv2.minAreaRect(hull)
            (cx, cy), (w, h), angle = rect
            x, y, bw, bh = cv2.boundingRect(cnt)
            
            objects.append({
                'bbox': (x, y, bw, bh),
                'center': (int(cx), int(cy)),
                'rect': rect,
                'contour': hull,
                'outer_contour': cnt,
                'hole_contour': hole_contour,
                'area': cv2.contourArea(hull),
                'is_donut': is_donut,
                'hole_ratio': hole_ratio
            })
        
        return objects

print("✓ ObjectDetectorV15")

# ============================================================
# DONUT GRASP SELECTOR
# ============================================================
class DonutGraspSelector:
    def __init__(self, pixels_per_mm):
        self.ppm = pixels_per_mm
    
    def analyze_object(self, obj):
        if obj.get('is_donut', False):
            return self._analyze_donut(obj)
        else:
            return self._analyze_solid(obj)
    
    def _analyze_donut(self, obj):
        outer = obj.get('outer_contour')
        hole = obj.get('hole_contour')
        if outer is None or hole is None:
            return self._analyze_solid(obj)
        
        M_outer = cv2.moments(outer)
        M_hole = cv2.moments(hole)
        if M_outer['m00'] == 0 or M_hole['m00'] == 0:
            return self._analyze_solid(obj)
        
        cx_outer = int(M_outer['m10'] / M_outer['m00'])
        cy_outer = int(M_outer['m01'] / M_outer['m00'])
        
        outer_rect = cv2.minAreaRect(outer)
        hole_rect = cv2.minAreaRect(hole)
        outer_radius = min(outer_rect[1]) / 2
        hole_radius = min(hole_rect[1]) / 2
        ring_thickness_px = outer_radius - hole_radius
        ring_thickness_mm = ring_thickness_px / self.ppm
        
        if ring_thickness_mm <= 0 or ring_thickness_mm > GRIPPER_MAX_WIDTH_MM:
            return self._analyze_solid(obj)
        
        grasps = []
        grasp_radius = (outer_radius + hole_radius) / 2
        
        for i, angle_deg in enumerate([0, 90, 180, 270]):
            angle_rad = np.radians(angle_deg)
            gx = int(cx_outer + grasp_radius * np.cos(angle_rad))
            gy = int(cy_outer + grasp_radius * np.sin(angle_rad))
            grasp_angle = self._normalize(angle_deg)
            lidar_offset = ring_thickness_px * 0.3
            lx = int(cx_outer + (grasp_radius + lidar_offset) * np.cos(angle_rad))
            ly = int(cy_outer + (grasp_radius + lidar_offset) * np.sin(angle_rad))
            
            grasps.append({
                'center': (gx, gy),
                'lidar_point': (lx, ly),
                'width_mm': ring_thickness_mm,
                'camera_angle': grasp_angle,
                'score': 1.0 - i * 0.1,
                'type': 'Donut-Edge',
                'position': ['Right', 'Bottom', 'Left', 'Top'][i],
                'is_donut_grasp': True
            })
        return grasps
    
    def _analyze_solid(self, obj):
        cnt = obj.get('contour')
        if cnt is None or len(cnt) < 5:
            return self._fallback(obj)
        
        pts = cnt.reshape(-1, 2).astype(np.float64)
        mean = np.mean(pts, axis=0)
        pts_centered = pts - mean
        cov = np.cov(pts_centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, idx]
        major = eigenvectors[:, 0]
        minor = eigenvectors[:, 1]
        angle = np.degrees(np.arctan2(major[1], major[0]))
        proj = np.dot(pts_centered, minor)
        width_mm = (np.max(proj) - np.min(proj)) / self.ppm
        cx, cy = int(mean[0]), int(mean[1])
        grasp_angle = self._normalize(angle + 90)
        
        if width_mm <= GRIPPER_MAX_WIDTH_MM:
            return [{'center': (cx, cy), 'lidar_point': (cx, cy), 'width_mm': width_mm,
                     'camera_angle': grasp_angle, 'score': 1.0, 'type': 'PCA-Solid', 'is_donut_grasp': False}]
        return self._fallback(obj)
    
    def _fallback(self, obj):
        rect = obj.get('rect')
        if not rect: return []
        (cx, cy), (w, h), angle = rect
        grip_w = min(w, h) / self.ppm
        grip_a = angle + 90 if w < h else angle
        if grip_w <= GRIPPER_MAX_WIDTH_MM:
            return [{'center': (int(cx), int(cy)), 'lidar_point': (int(cx), int(cy)), 'width_mm': grip_w,
                     'camera_angle': self._normalize(grip_a), 'score': 0.6, 'type': 'Rect-Fallback', 'is_donut_grasp': False}]
        return []
    
    def _normalize(self, a):
        while a > 90: a -= 180
        while a < -90: a += 180
        return a

print("✓ DonutGraspSelector")
