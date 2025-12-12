# =============================================================================
# 🎯 Advanced Grasp Detection v6
# =============================================================================
# Features:
# - YOLO + Grid for precise object sizing
# - Smart auto grasp selection with manual override
# - Improved depth accuracy
# - No margin gripping
# =============================================================================

# %% [markdown]
# # 🎯 Advanced Grasp Detection v6
# 
# ## Features
# | Feature | Description |
# |---------|-------------|
# | **🔍 YOLO Detection** | Object detection + Grid sizing |
# | **🎯 Smart Grasp** | Auto grasp point selection |
# | **📏 Precise Sizing** | Contour-based exact measurements |
# | **🦾 Tight Grip** | No margin - grip at exact size |

# %% [markdown]
# ## 1️⃣ Imports

# %%
import sys
import cv2
import numpy as np
import time
import socket
import serial
import torch
from collections import deque
from ultralytics import YOLO

sys.path.append('Depth-Anything-V2')

print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
print("✓ Imports loaded")

# %% [markdown]
# ## 2️⃣ Hardware Configuration

# %%
ROBOT_IP = '192.168.1.6'
ESP32_PORT = 'COM9'
ESP32_BAUDRATE = 115200
CAMERA_ID = 2

HOMOGRAPHY_MATRIX = np.array([
    [0.005703976266962427, -0.3265299161278153, 88.58634169557483],
    [-0.47704058225560797, 0.015355046930804153, 172.0941543570439],
    [-0.00029949919510557677, 0.00018728182448344945, 1.0],
], dtype=np.float32)

print("✓ Hardware config loaded")

# %% [markdown]
# ---
# # 🔧 CALIBRATION SECTION
# ---
# 
# ## 📐 Calibration 1: PIXELS_PER_MM
# 1. วางไม้บรรทัดบนพื้นที่ทำงาน
# 2. ลากเส้นจากจุดหนึ่งไปอีกจุด
# 3. ใส่ขนาดจริง (mm)
# 4. Copy ค่าไปใส่ Section 3

# %%
# === PIXELS_PER_MM CALIBRATION ===
def run_pixel_calibration():
    print("="*50)
    print("📐 PIXELS_PER_MM CALIBRATION")
    print("Drag line on ruler | ENTER=Calculate | Q=Quit")
    print("="*50)
    
    drawing = False
    start_pt = None
    end_pt = None
    px_dist = 0
    
    def callback(event, x, y, flags, param):
        nonlocal drawing, start_pt, end_pt, px_dist
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_pt = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            end_pt = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            end_pt = (x, y)
            px_dist = np.sqrt((end_pt[0]-start_pt[0])**2 + (end_pt[1]-start_pt[1])**2)
            print(f"📏 Distance: {px_dist:.1f} px")
    
    cap = cv2.VideoCapture(CAMERA_ID)
    cv2.namedWindow('Pixel Calibration')
    cv2.setMouseCallback('Pixel Calibration', callback)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        if start_pt and end_pt:
            cv2.line(frame, start_pt, end_pt, (0,255,0), 2)
        cv2.imshow('Pixel Calibration', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == 13 and px_dist > 0:
            real_mm = float(input("📏 Real size (mm): "))
            ppm = px_dist / real_mm
            print(f"✅ PIXELS_PER_MM = {ppm:.4f}")
    cap.release()
    cv2.destroyAllWindows()

# Uncomment to run: run_pixel_calibration()

# %% [markdown]
# ## 📏 Calibration 2: DEPTH_Z_SCALE
# 1. กด C calibrate พื้น (เอาวัตถุออก)
# 2. วางวัตถุที่รู้ความสูง แล้วคลิก

# %%
# === DEPTH_Z_SCALE CALIBRATION ===
# Run after loading depth model (Section 4)
# Uncomment and run when needed

# %% [markdown]
# ## 🦾 Calibration 3: Gripper Test
# ทดสอบว่า gripper width mapping ถูกต้อง

# %%
# === GRIPPER TEST ===
# Run after connecting gripper (Section 6)

# %% [markdown]
# ---
# ## 3️⃣ Configuration (ใส่ค่าที่ Calibrate แล้ว)
# ---

# %%
# === CALIBRATED VALUES ===
PIXELS_PER_MM = 2.2167      # จาก Calibration 1
DEPTH_Z_SCALE = 57.428993   # จาก Calibration 2

# === Z Heights ===
Z_FLOOR = -64
Z_SAFE = -40
Z_APPROACH = -55

# === Drop Position ===
DROP_POS = (-253.07, 115.17, -17.07, -62.78)

# === Gripper (NO MARGIN - คีบแน่น) ===
GRIPPER_SERVO_OPEN_ANGLE = 22
GRIPPER_SERVO_CLOSE_ANGLE = 96
GRIPPER_MAX_WIDTH_MM = 54
GRIPPER_MIN_WIDTH_MM = 0
GRIPPER_OPEN_MARGIN_MM = 5   # เปิดกว้างกว่าเล็กน้อย
GRIPPER_GRIP_MARGIN_MM = 0   # คีบตรงตามขนาด

# === Detection ===
MIN_OBJECT_AREA = 1000
YOLO_CONFIDENCE = 0.25

# === Depth Model ===
DEPTH_MODEL_PATH = 'Depth-Anything-V2/checkpoints/depth_anything_v2_vits.pth'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# === Grid Display ===
SHOW_GRID = True
GRID_SIZE_MM = 20  # Grid spacing in mm

print("✓ Configuration loaded")
print(f"  PIXELS_PER_MM: {PIXELS_PER_MM}")
print(f"  GRIP_MARGIN: {GRIPPER_GRIP_MARGIN_MM}mm (tight grip)")

# %% [markdown]
# ## 4️⃣ Load Models

# %%
from depth_anything_v2.dpt import DepthAnythingV2

model_configs = {
    'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
}

print("Loading DepthAnything V2...")
depth_model = DepthAnythingV2(**model_configs['vits'])
depth_model.load_state_dict(torch.load(DEPTH_MODEL_PATH, map_location='cpu'))
depth_model = depth_model.to(DEVICE).eval()
print(f"✅ Depth model on {DEVICE}")

print("Loading YOLOv8...")
yolo_model = YOLO('yolov8n.pt')
print("✅ YOLO loaded")

# %% [markdown]
# ## 5️⃣ Classes Definition

# %%
class SmartGripperController:
    """Gripper with NO MARGIN - tight grip"""
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
            print(f"✅ Gripper connected on {self.port}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.serial:
            self.serial.close()
    
    def send_command(self, cmd):
        if self.serial:
            self.serial.write((cmd + '\n').encode())
            time.sleep(0.3)
    
    def mm_to_angle(self, width_mm):
        width = max(0.0, min(54.0, width_mm))
        angle = np.interp(width, self.CALIB_WIDTHS[::-1], self.CALIB_ANGLES[::-1])
        return int(round(angle))
    
    def open_for_object(self, width_mm):
        self.target_width = width_mm
        open_w = min(54.0, width_mm + GRIPPER_OPEN_MARGIN_MM)
        angle = self.mm_to_angle(open_w)
        print(f"🦾 Open: {width_mm:.1f}mm → {open_w:.1f}mm ({angle}°)")
        self.send_command(f'G{angle}')
    
    def grip_object(self, width_mm):
        # NO MARGIN - grip at exact size
        grip_w = max(0.0, width_mm - GRIPPER_GRIP_MARGIN_MM)
        angle = self.mm_to_angle(grip_w)
        print(f"🦾 Grip: {width_mm:.1f}mm ({angle}°)")
        self.send_command(f'G{angle}')
    
    def release(self):
        open_w = min(54.0, (self.target_width or 30) + 10)
        angle = self.mm_to_angle(open_w)
        self.send_command(f'G{angle}')
        self.target_width = None


class DobotControllerTCP:
    def __init__(self, homography_matrix=None):
        self.dashboard_port = 29999
        self.sock = None
        self.H = homography_matrix
        
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
            print(f"Connection Error: {e}")
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
        if self.H is None:
            return None, None
        pt = np.array([u, v, 1], dtype=np.float32)
        res = np.dot(self.H, pt)
        return res[0]/res[2], res[1]/res[2]


class PreciseSizeDetector:
    """YOLO + Contour for precise sizing with Grid overlay"""
    
    def __init__(self, yolo_model, pixels_per_mm):
        self.yolo = yolo_model
        self.ppm = pixels_per_mm
        self.bg_gray = None
    
    def set_background(self, frame):
        self.bg_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.bg_gray = cv2.GaussianBlur(self.bg_gray, (5,5), 0)
        print("✅ Background set")
    
    def detect(self, frame):
        """Detect objects using YOLO + contour refinement"""
        objects = []
        
        # YOLO detection
        results = self.yolo(frame, conf=YOLO_CONFIDENCE, verbose=False)
        
        for r in results:
            for box in r.boxes:
                x1,y1,x2,y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                # Refine with contour
                roi = frame[y1:y2, x1:x2]
                if roi.size == 0:
                    continue
                    
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    cnt = max(contours, key=cv2.contourArea)
                    cnt += np.array([x1, y1])  # Offset to frame coords
                    rect = cv2.minAreaRect(cnt)
                    cx, cy = int(rect[0][0]), int(rect[0][1])
                    
                    objects.append({
                        'bbox': (x1, y1, x2-x1, y2-y1),
                        'center': (cx, cy),
                        'rect': rect,
                        'rect_size': rect[1],
                        'rect_angle': rect[2],
                        'contour': cnt,
                        'conf': conf,
                        'class': cls,
                        'area': cv2.contourArea(cnt)
                    })
        
        # Fallback to edge detection if YOLO finds nothing
        if not objects:
            objects = self.edge_detect(frame)
        
        return objects
    
    def edge_detect(self, frame):
        """Fallback: edge-based detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blur, 50, 150)
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        objects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > MIN_OBJECT_AREA:
                hull = cv2.convexHull(cnt)
                rect = cv2.minAreaRect(hull)
                x,y,w,h = cv2.boundingRect(hull)
                cx, cy = x + w//2, y + h//2
                
                objects.append({
                    'bbox': (x,y,w,h),
                    'center': (cx, cy),
                    'rect': rect,
                    'rect_size': rect[1],
                    'rect_angle': rect[2],
                    'contour': hull,
                    'area': area
                })
        
        return sorted(objects, key=lambda o: o['area'], reverse=True)
    
    def draw_grid(self, frame):
        """Draw reference grid"""
        if not SHOW_GRID:
            return frame
        h, w = frame.shape[:2]
        grid_px = int(GRID_SIZE_MM * self.ppm)
        
        for x in range(0, w, grid_px):
            cv2.line(frame, (x,0), (x,h), (50,50,50), 1)
        for y in range(0, h, grid_px):
            cv2.line(frame, (0,y), (w,y), (50,50,50), 1)
        
        cv2.putText(frame, f"Grid: {GRID_SIZE_MM}mm", (10, h-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100,100,100), 1)
        return frame


class SmartGraspSelector:
    """Auto select best grasp point + generate alternatives"""
    
    def __init__(self, pixels_per_mm):
        self.ppm = pixels_per_mm
    
    def analyze_object(self, obj):
        """Analyze object shape and return grasp candidates"""
        w, h = obj['rect_size']
        angle = obj['rect_angle']
        cx, cy = obj['center']
        
        # Aspect ratio
        aspect = max(w,h) / (min(w,h) + 0.001)
        
        # Check if ring-shaped
        is_ring = self.detect_ring(obj)
        
        grasps = []
        
        if aspect > 2.0:
            # Long object → grasp narrow side
            if w < h:
                grip_w = w / self.ppm
                grip_angle = angle + 90
            else:
                grip_w = h / self.ppm
                grip_angle = angle
            
            grasps.append({
                'center': (cx, cy),
                'width_mm': grip_w,
                'angle': self.normalize_angle(grip_angle),
                'score': 1.0,  # Best
                'type': 'narrow_side'
            })
            
            # Alternative: 90° rotated
            alt_angle = grip_angle + 90
            alt_w = max(w,h) / self.ppm
            if alt_w <= GRIPPER_MAX_WIDTH_MM:
                grasps.append({
                    'center': (cx, cy),
                    'width_mm': alt_w,
                    'angle': self.normalize_angle(alt_angle),
                    'score': 0.5,
                    'type': 'alternative'
                })
        
        elif is_ring:
            # Ring → multiple angles around center
            inner_w = self.estimate_ring_width(obj)
            for i in range(4):
                a = i * 45
                grasps.append({
                    'center': (cx, cy),
                    'width_mm': inner_w,
                    'angle': a,
                    'score': 1.0 if i == 0 else 0.8,
                    'type': 'ring'
                })
        
        else:
            # General → grasp shorter side
            if w < h:
                grip_w = w / self.ppm
                grip_angle = angle + 90
            else:
                grip_w = h / self.ppm
                grip_angle = angle
            
            grasps.append({
                'center': (cx, cy),
                'width_mm': grip_w,
                'angle': self.normalize_angle(grip_angle),
                'score': 1.0,
                'type': 'default'
            })
            
            # + perpendicular
            perp_angle = grip_angle + 90
            perp_w = max(w,h) / self.ppm
            if perp_w <= GRIPPER_MAX_WIDTH_MM:
                grasps.append({
                    'center': (cx, cy),
                    'width_mm': perp_w,
                    'angle': self.normalize_angle(perp_angle),
                    'score': 0.6,
                    'type': 'perpendicular'
                })
        
        return grasps
    
    def detect_ring(self, obj):
        """Detect if object is ring-shaped"""
        cnt = obj.get('contour')
        if cnt is None:
            return False
        area = cv2.contourArea(cnt)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / (hull_area + 0.001)
        return solidity < 0.7  # Ring has low solidity
    
    def estimate_ring_width(self, obj):
        """Estimate graspable width for ring"""
        w, h = obj['rect_size']
        outer = max(w, h) / self.ppm
        # Estimate inner ~60% of outer
        return outer * 0.3
    
    def normalize_angle(self, angle):
        while angle > 90: angle -= 180
        while angle < -90: angle += 180
        return angle


class RobustDepthEstimator:
    """Multi-sample + temporal averaging depth"""
    
    def __init__(self, model, device='cpu', history_size=5):
        self.model = model
        self.device = device
        self.floor_depth = None
        self.history = deque(maxlen=history_size)
    
    def estimate_depth(self, frame):
        return self.model.infer_image(frame)
    
    def calibrate_floor(self, frame):
        depth = self.estimate_depth(frame)
        h, w = depth.shape
        center = depth[h//3:2*h//3, w//3:2*w//3]
        self.floor_depth = np.median(center)
        print(f"✅ Floor depth: {self.floor_depth:.4f}")
        return self.floor_depth
    
    def get_object_height(self, depth_map, obj, scale):
        if self.floor_depth is None:
            return 0
        
        x, y, w, h = obj['bbox']
        region = depth_map[y:y+h, x:x+w]
        if region.size == 0:
            return 0
        
        # Multi-sample: center + corners
        samples = []
        samples.append(np.median(region))
        
        # 4 quadrant samples
        qh, qw = h//4, w//4
        if qh > 0 and qw > 0:
            samples.append(np.median(region[:qh, :qw]))
            samples.append(np.median(region[:qh, -qw:]))
            samples.append(np.median(region[-qh:, :qw]))
            samples.append(np.median(region[-qh:, -qw:]))
        
        obj_depth = np.median(samples)
        diff = obj_depth - self.floor_depth
        height = max(0, diff * scale)
        
        # Temporal averaging
        self.history.append(height)
        return np.median(self.history)
    
    def calculate_z(self, height_mm):
        z = Z_FLOOR + (height_mm * 0.5)
        return max(Z_FLOOR, min(Z_SAFE, z))

print("✓ All classes loaded")

# %% [markdown]
# ## 6️⃣ Initialize & Connect

# %%
gripper = SmartGripperController(port=ESP32_PORT, baudrate=ESP32_BAUDRATE)
robot = DobotControllerTCP(homography_matrix=HOMOGRAPHY_MATRIX)
detector = PreciseSizeDetector(yolo_model, PIXELS_PER_MM)
grasp_selector = SmartGraspSelector(PIXELS_PER_MM)
depth_estimator = RobustDepthEstimator(depth_model, device=DEVICE)
print("✓ Components initialized")

# %%
gripper.connect()

# %%
robot.connect(ROBOT_IP)

# %% [markdown]
# ## 📷 Capture Background (Optional)

# %%
print("="*50)
print("📷 BACKGROUND CALIBRATION (Optional)")
print("SPACE = Capture | Q = Skip")
print("="*50)

cap = cv2.VideoCapture(CAMERA_ID)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    cv2.putText(frame, "SPACE=Capture Background | Q=Skip", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
    cv2.imshow('Background', frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord(' '):
        detector.set_background(frame)
        depth_estimator.calibrate_floor(frame)
        break
    elif key == ord('q'):
        print("Skipped background capture")
        break
cap.release()
cv2.destroyAllWindows()

# %% [markdown]
# ---
# # 🎯 MAIN PICK-AND-PLACE
# ---

# %%
# =============================================================================
# 🎯 PICK-AND-PLACE v6
# =============================================================================
selected_object = None
selected_grasp = None
detected_objects = []
current_grasps = []
current_depth = None

def mouse_callback(event, x, y, flags, param):
    global selected_object, selected_grasp, current_grasps
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # First check if clicking on a grasp point
        for g in current_grasps:
            gx, gy = g['center']
            if abs(x - gx) < 20 and abs(y - gy) < 20:
                selected_grasp = g
                print(f"\n🎯 Grasp: W={g['width_mm']:.1f}mm A={g['angle']:.1f}° ({g['type']})")
                return
        
        # Otherwise select object
        for obj in detected_objects:
            bx, by, bw, bh = obj['bbox']
            if bx <= x <= bx+bw and by <= y <= by+bh:
                selected_object = obj
                current_grasps = grasp_selector.analyze_object(obj)
                selected_grasp = current_grasps[0] if current_grasps else None
                if selected_grasp:
                    print(f"\n📦 Object: {len(current_grasps)} grasps available")
                    print(f"   Best: W={selected_grasp['width_mm']:.1f}mm A={selected_grasp['angle']:.1f}°")
                break

def draw_grasps(frame, obj, grasps, selected):
    """Draw grasp candidates on frame"""
    for g in grasps:
        cx, cy = g['center']
        angle = g['angle']
        is_sel = (selected and g == selected)
        
        # Color: green=best, yellow=alt, red=selected
        if is_sel:
            color = (0, 0, 255)
            thick = 3
        elif g['score'] >= 1.0:
            color = (0, 255, 0)
            thick = 2
        else:
            color = (0, 255, 255)
            thick = 1
        
        # Draw grip line
        dx = int(30 * np.cos(np.radians(angle)))
        dy = int(30 * np.sin(np.radians(angle)))
        cv2.line(frame, (cx-dx, cy-dy), (cx+dx, cy+dy), color, thick)
        cv2.circle(frame, (cx, cy), 5, color, -1)

def pick_with_grasp(obj, grasp):
    """Execute pick using selected grasp"""
    cx, cy = grasp['center']
    grip_w = grasp['width_mm']
    angle = grasp['angle']
    robot_r = -angle  # Convert to robot frame
    
    robot_x, robot_y = robot.pixel_to_robot(cx, cy)
    height = depth_estimator.get_object_height(current_depth, obj, DEPTH_Z_SCALE) if current_depth is not None else 0
    z_grasp = depth_estimator.calculate_z(height)
    
    print(f"\n🤖 Pick: W={grip_w:.1f}mm R={robot_r:.1f}° Z={z_grasp:.1f}")
    
    # Safe position first
    print("🔄 Safe position...")
    robot.joint_move_and_wait(0, 0, 0, 0, 3)
    
    gripper.open_for_object(grip_w)
    time.sleep(1)
    
    robot.move_to_and_wait(robot_x, robot_y, Z_APPROACH, robot_r, 3)
    robot.move_to_and_wait(robot_x, robot_y, z_grasp, robot_r, 2)
    
    gripper.grip_object(grip_w)
    time.sleep(1.5)
    
    robot.move_to_and_wait(robot_x, robot_y, Z_SAFE, robot_r, 2)
    robot.move_to_and_wait(*DROP_POS[:3], DROP_POS[3], 3)
    
    gripper.release()
    time.sleep(1)
    robot.home()
    print("✅ Complete!")

# Main loop
cap = cv2.VideoCapture(CAMERA_ID)
cv2.namedWindow('Pick v6')
cv2.setMouseCallback('Pick v6', mouse_callback)

frame_count = 0
print("="*50)
print("🎯 PICK v6")
print("Click=Select Object | Click Grasp=Change")
print("SPACE=Execute | G=Toggle Grid | Q=Quit")
print("="*50)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    # Draw grid
    frame = detector.draw_grid(frame)
    
    # Detect
    frame_count += 1
    if frame_count % 10 == 0:
        current_depth = depth_estimator.estimate_depth(frame)
    
    detected_objects = detector.detect(frame)
    
    # Draw objects
    for obj in detected_objects:
        x, y, w, h = obj['bbox']
        is_sel = (selected_object and obj['center'] == selected_object['center'])
        color = (0, 0, 255) if is_sel else (0, 255, 0)
        
        # Bounding box
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # Min area rect
        if 'rect' in obj:
            box = cv2.boxPoints(obj['rect'])
            cv2.drawContours(frame, [np.int32(box)], 0, color, 1)
        
        # Size info
        rect_w, rect_h = obj['rect_size']
        w_mm = min(rect_w, rect_h) / PIXELS_PER_MM
        cv2.putText(frame, f"W:{w_mm:.0f}mm", (x, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Draw grasps for selected object
    if selected_object and current_grasps:
        draw_grasps(frame, selected_object, current_grasps, selected_grasp)
    
    # Status bar
    cv2.rectangle(frame, (0, 0), (640, 35), (30, 30, 30), -1)
    status = f"Objects:{len(detected_objects)} | Click=Select | SPACE=Pick | G=Grid | Q=Quit"
    cv2.putText(frame, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)
    
    if selected_grasp:
        cv2.putText(frame, f"[GRASP: W={selected_grasp['width_mm']:.1f}mm - SPACE to pick]",
                   (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
    
    cv2.imshow('Pick v6', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        selected_object = None
        selected_grasp = None
        current_grasps = []
    elif key == ord('g'):
        SHOW_GRID = not SHOW_GRID
    elif key == ord('h'):
        robot.home()
    elif key == ord(' ') and selected_object and selected_grasp:
        pick_with_grasp(selected_object, selected_grasp)
        selected_object = None
        selected_grasp = None
        current_grasps = []

cap.release()
cv2.destroyAllWindows()

# %%
gripper.disconnect()
print("✅ Done")
