# คู่มือการใช้งานจริงกับ Dobot MG400 🤖

**สำหรับ: นำระบบ Grasp Detection ไปใช้งานจริงกับหุ่นยนต์**

---

## 📋 สารบัญ

1. [เตรียมอุปกรณ์](#1-เตรียมอุปกรณ์)
2. [ติดตั้งซอฟต์แวร์](#2-ติดตั้งซอฟต์แวร์)
3. [ตั้งค่า Workspace](#3-ตั้งค่า-workspace)
4. [Calibrate Camera](#4-calibrate-camera-สำคัญมาก)
5. [เชื่อมต่อหุ่นยนต์](#5-เชื่อมต่อหุ่นยนต์)
6. [ทดสอบการจับวัตถุ](#6-ทดสอบการจับวัตถุ)
7. [Troubleshooting](#7-troubleshooting)
8. [Safety Guidelines](#8-safety-guidelines)

---

## 1. เตรียมอุปกรณ์

### ✅ Checklist อุปกรณ์

#### Hardware
- [ ] **Dobot MG400** พร้อม Gripper
- [ ] **Webcam USB** (ความละเอียดอย่างน้อย 640x480)
- [ ] **Computer/Laptop** (Windows/Linux)
  - RAM: อย่างน้อย 8GB
  - GPU: แนะนำ (แต่ไม่บังคับ)
- [ ] **Power Supply** สำหรับ robot
- [ ] **Ethernet Cable** หรือ WiFi สำหรับเชื่อมต่อ robot
- [ ] **Workspace Setup**:
  - โต๊ะหรือพื้นที่ทำงานเรียบ
  - แสงสว่างเพียงพอ (หลีกเลี่ยงเงาหรือแสงสะท้อน)
  - พื้นหลังเรียบ (ควรเป็นสีเดียว)

#### Software
- [ ] Python 3.8+ installed
- [ ] Jupyter Notebook
- [ ] Dobot Studio (สำหรับทดสอบ robot)

### 📸 ติดตั้ง Camera

**ตำแหน่งแนะนำ:**
```
         [Camera]
            ↓
      +-----------+
      |  Workspace |
      |           |
      |  [Robot]  |
      +-----------+
```

**หลักการ:**
1. ติดตั้ง camera **ด้านบน** workspace (มองลงมา)
2. ระยะห่าง: 40-60 cm จากพื้นผิวงาน
3. มุมกล้อง: ตั้งฉากกับพื้นผิว (90°)
4. ให้ camera เห็นพื้นที่ทำงานของ robot ทั้งหมด

**วิธีติดตั้ง:**
- ใช้ tripod, clamp, หรือ bracket ติดกับโครงสร้าง
- **ห้ามติดกับ robot arm!** (จะเคลื่อนที่ตาม)
- ตรวจสอบว่าสายไม่กีดขวางการเคลื่อนที่

---

## 2. ติดตั้งซอฟต์แวร์

### ขั้นตอนที่ 1: ติดตั้ง Python Dependencies

```bash
# ไปที่ folder notebook_v3
cd c:\Users\CPE KMUTT\Music\Artificial_MonoGrasp\notebook_v3

# ติดตั้ง dependencies พื้นฐาน
pip install -r requirements.txt

# ติดตั้ง pydobot สำหรับควบคุม Dobot MG400
pip install pydobot
```

### ขั้นตอนที่ 2: ติดตั้ง Dobot Studio

1. ดาวน์โหลดจาก: https://www.dobot.cc/downloadcenter/mg400.html
2. ติดตั้งตาม wizard
3. **ไว้ใช้ทดสอบ robot และ homing**

### ขั้นตอนที่ 3: ตรวจสอบ Camera

```bash
# เปิด Python และทดสอบ
python
```

```python
import cv2

# เปลี่ยน 0 เป็น 1, 2 ถ้าไม่ใช่ camera หลัก
cap = cv2.VideoCapture(0)

# ถ้า True = camera ทำงาน
print(cap.isOpened())

ret, frame = cap.read()
print(f"Frame shape: {frame.shape}")  # ควรได้ (480, 640, 3) หรือใกล้เคียง

cap.release()
```

**ถ้าไม่เจอ camera:**
- ลองเปลี่ยน `CAMERA_ID` ใน `config.py` (0, 1, 2...)
- ตรวจสอบ USB connection
- ตรวจสอบ driver (Windows: Device Manager)

---

## 3. ตั้งค่า Workspace

### Layout แนะนำ

```
┌───────────────────────────────────┐
│                                   │
│        [Camera View]              │
│                                   │
│  ┌─────────────────────┐         │
│  │                     │         │
│  │   Safe Workspace    │         │
│  │   (30x30 cm)        │         │
│  │                     │         │
│  │      [Objects]      │         │
│  │                     │         │
│  └─────────────────────┘         │
│                                   │
│         [Robot Base]              │
└───────────────────────────────────┘
```

### กำหนด Robot Workspace Limits

1. **เปิด Dobot Studio**
2. **Home robot** (กดปุ่ม Home)
3. **บันทึกขอบเขต workspace**:
   - เคลื่อน robot arm ไปที่มุม 4 มุมของพื้นที่ทำงาน
   - บันทึก coordinates (X, Y, Z) แต่ละมุม

**ตัวอย่าง:**
```
มุมซ้ายบน:    X=200, Y=200,  Z=0
มุมขวาบน:     X=400, Y=200,  Z=0
มุมซ้ายล่าง:  X=200, Y=-200, Z=0
มุมขวาล่าง:   X=400, Y=-200, Z=0
```

4. **แก้ไข `config.py`**:
```python
# Robot workspace limits (mm)
ROBOT_X_MIN = 200
ROBOT_X_MAX = 400
ROBOT_Y_MIN = -200
ROBOT_Y_MAX = 200
ROBOT_Z_MIN = -100
ROBOT_Z_MAX = 100
```

### ตั้งค่าแสง

- ใช้แสง LED แบบกระจาย (diffused)
- หลีกเลี่ยงแสงแดดตรง หรือแสงสะท้อนแรง
- ทดสอบด้วย camera ว่าไม่มีเงาหนา

---

## 4. Calibrate Camera (สำคัญมาก!) 🎯

**ทำไมต้อง calibrate?**
- แปลง pixel coordinates → robot coordinates (mm)
- ถ้าไม่ calibrate = robot จับพลาด!

### วิธี Calibration แบบง่าย (Checkerboard)

#### ขั้นตอนที่ 1: เตรียม Checkerboard

1. พิมพ์ checkerboard pattern (7x7 หรือ 9x6 squares)
2. วางบน workspace ที่ robot จะทำงาน
3. ถ่ายภาพด้วย camera

#### ขั้นตอนที่ 2: หา Camera Intrinsics

```python
import cv2
import numpy as np

# ขนาดของ checkerboard (จำนวนมุมภายใน)
pattern_size = (6, 8)  # แก้ตามของจริง
square_size = 25  # มม. ต่อช่อง

# Capture หลายภาพจากมุมต่างๆ
images = []  # โหลดภาพที่ถ่ายไว้

# Run camera calibration
# (โค้ดเต็มมีใน OpenCV docs)
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(...)

print("Camera Matrix:")
print(camera_matrix)
print("\nDistortion Coefficients:")
print(dist_coeffs)
```

#### ขั้นตอนที่ 3: สร้าง Transformation Matrix (แบบง่าย)

**วิธีที่ง่ายที่สุด: 4-Point Method**

1. **วาง marker 4 จุด** บน workspace:
   ```
   A (มุมซ้ายบน)      B (มุมขวาบน)
   
   
   C (มุมซ้ายล่าง)    D (มุมขวาล่าง)
   ```

2. **บันทึก pixel coordinates**:
   ```python
   # ถ่ายภาพและคลิกหา coordinates
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   
   # ใช้ mouse callback หรือ manual
   pixel_points = [
       (100, 50),   # A
       (540, 50),   # B
       (100, 430),  # C
       (540, 430)   # D
   ]
   ```

3. **วัด robot coordinates จริง** (ใช้ Dobot Studio):
   ```python
   robot_points = [
       (200, 200),    # A (X, Y in mm)
       (400, 200),    # B
       (200, -200),   # C
       (400, -200)    # D
   ]
   ```

4. **คำนวณ transformation**:
   ```python
   import numpy as np
   
   # Homography matrix
   pixel_pts = np.array(pixel_points, dtype=np.float32)
   robot_pts = np.array(robot_points, dtype=np.float32)
   
   H, status = cv2.findHomography(pixel_pts, robot_pts)
   
   print("Homography Matrix:")
   print(H)
   ```

5. **ใช้งาน**:
   ```python
   def pixel_to_robot(pixel_x, pixel_y, H):
       """แปลง pixel → robot coordinates"""
       pixel_point = np.array([[pixel_x, pixel_y]], dtype=np.float32)
       pixel_point = pixel_point.reshape(-1, 1, 2)
       
       robot_point = cv2.perspectiveTransform(pixel_point, H)
       
       robot_x = robot_point[0][0][0]
       robot_y = robot_point[0][0][1]
       
       return robot_x, robot_y
   
   # ทดสอบ
   robot_x, robot_y = pixel_to_robot(320, 240, H)
   print(f"Robot coords: ({robot_x:.1f}, {robot_y:.1f}) mm")
   ```

6. **บันทึกใน `config.py`**:
   ```python
   # Camera to robot calibration
   HOMOGRAPHY_MATRIX = [
       [1.2, 0.01, -150],
       [0.02, 1.3, 200],
       [0.0001, 0.0002, 1]
   ]
   # หรือบันทึกเป็น .npy file
   ```

### ทดสอบ Calibration

```python
# วางวัตถุที่ตำแหน่งทราบ
# เช่น (300, 0) บน robot
# ดูว่า detection ได้ pixel coordinates เท่าไหร่
# แปลงกลับด้วย transformation
# ควรได้ใกล้เคียง (300, 0)

tolerance = 10  # mm
if abs(calculated_x - 300) < tolerance:
    print("✓ Calibration OK!")
else:
    print("✗ Need recalibration")
```

---

## 5. เชื่อมต่อหุ่นยนต์

### ขั้นตอนที่ 1: เชื่อมต่อ Network

**วิธีที่ 1: Ethernet (แนะนำ)**
1. เสียบสาย ethernet จาก robot → computer
2. ตั้งค่า IP:
   - Robot default IP: `192.168.1.6`
   - Computer IP: `192.168.1.xxx` (เช่น `192.168.1.100`)
   
**Windows:**
```
Control Panel → Network → Change Adapter Settings
→ Right-click Ethernet → Properties → IPv4
→ ตั้ง IP: 192.168.1.100
→ Subnet: 255.255.255.0
```

**วิธีที่ 2: WiFi**
1. เชื่อมต่อ robot กับ WiFi ผ่าน Dobot Studio
2. บันทึก IP address ที่ได้

### ขั้นตอนที่ 2: ทดสอบการเชื่อมต่อ

```bash
# Test ping
ping 192.168.1.6

# ควรได้ Reply
```

### ขั้นตอนที่ 3: ทดสอบควบคุม Robot (Python)

```python
from pydobot import Dobot

# เชื่อมต่อ
robot = Dobot(port='COM3')  # Windows
# robot = Dobot(port='/dev/ttyUSB0')  # Linux

# ถ้าเชื่อมต่อผ่าน TCP/IP:
# import socket
# robot = Dobot('192.168.1.6', port=29999)

# Home robot
robot.home()

# เคลื่อนที่ทดสอบ
robot.move_to(250, 0, 50, 0)  # X, Y, Z, R

# อ่าน position
pose = robot.pose()
print(f"Current position: {pose}")

# ปิดการเชื่อมต่อ
robot.close()
```

**ถ้า error:**
- Check COM port (Device Manager → Ports)
- Check IP address ถูกต้อง
- ลอง restart robot
- ตรวจสอบ firewall

---

## 6. ทดสอบการจับวัตถุ

### สร้าง Robot Control Module

สร้างไฟล์ `robot_control.py` ใน `notebook_v3/`:

```python
"""
Robot Control for Dobot MG400
"""

import numpy as np
from pydobot import Dobot
import time


class DobotController:
    """Simple Dobot MG400 controller"""
    
    def __init__(self, config, homography_matrix):
        self.config = config
        self.H = np.array(homography_matrix)
        self.robot = None
        self.is_connected = False
    
    def connect(self, port_or_ip):
        """Connect to robot"""
        try:
            self.robot = Dobot(port=port_or_ip)
            self.is_connected = True
            print("✓ Robot connected")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def home(self):
        """Home robot"""
        if not self.is_connected:
            print("Not connected")
            return False
        
        self.robot.home()
        print("✓ Robot homed")
        return True
    
    def pixel_to_robot(self, pixel_x, pixel_y):
        """Convert pixel to robot coordinates"""
        pixel_point = np.array([[pixel_x, pixel_y]], dtype=np.float32)
        pixel_point = pixel_point.reshape(-1, 1, 2)
        
        robot_point = cv2.perspectiveTransform(pixel_point, self.H)
        
        robot_x = float(robot_point[0][0][0])
        robot_y = float(robot_point[0][0][1])
        
        # Validate workspace limits
        robot_x = np.clip(robot_x, self.config.ROBOT_X_MIN, self.config.ROBOT_X_MAX)
        robot_y = np.clip(robot_y, self.config.ROBOT_Y_MIN, self.config.ROBOT_Y_MAX)
        
        return robot_x, robot_y
    
    def execute_grasp(self, grasp, depth_value):
        """Execute a grasp"""
        if not self.is_connected:
            print("Not connected")
            return False
        
        # Convert grasp center to robot coords
        cy, cx = grasp.center
        robot_x, robot_y = self.pixel_to_robot(cx, cy)
        
        # Calculate Z based on depth
        # (ต้องปรับตามการ calibrate)
        robot_z = 50  # mm above surface
        
        # Calculate rotation from grasp angle
        robot_r = np.degrees(grasp.angle)
        
        print(f"\nExecuting grasp:")
        print(f"  Pixel: ({cx:.0f}, {cy:.0f})")
        print(f"  Robot: ({robot_x:.1f}, {robot_y:.1f}, {robot_z:.1f})")
        print(f"  Angle: {robot_r:.1f}°")
        print(f"  Quality: {grasp.quality:.3f}")
        
        try:
            # 1. Move to safe height
            self.robot.move_to(robot_x, robot_y, 100, robot_r)
            time.sleep(1)
            
            # 2. Open gripper
            self.robot.suck(False)  # หรือใช้ gripper command
            time.sleep(0.5)
            
            # 3. Move down to grasp
            self.robot.move_to(robot_x, robot_y, robot_z, robot_r)
            time.sleep(1)
            
            # 4. Close gripper
            self.robot.suck(True)  # หรือใช้ gripper command
            time.sleep(1)
            
            # 5. Lift up
            self.robot.move_to(robot_x, robot_y, 100, robot_r)
            time.sleep(1)
            
            # 6. Move to drop position (กำหนดเอง)
            self.robot.move_to(300, 200, 50, 0)
            time.sleep(1)
            
            # 7. Release
            self.robot.suck(False)
            time.sleep(0.5)
            
            print("✓ Grasp executed successfully!")
            return True
            
        except Exception as e:
            print(f"✗ Grasp execution failed: {e}")
            return False
    
    def emergency_stop(self):
        """Emergency stop"""
        if self.robot:
            self.robot.close()
    
    def disconnect(self):
        """Disconnect robot"""
        if self.robot:
            self.robot.close()
            self.is_connected = False
            print("Robot disconnected")
```

### Integration Notebook

สร้าง `robot_demo.ipynb`:

```python
# Cell 1: Imports
import cv2
import numpy as np
import config
from simple_pipeline import SimplePipeline
from object_detector import ObjectDetector
from depth_estimator import DepthEstimator
from rule_based_grasp import RuleBasedGraspGenerator
from robot_control import DobotController
from visualization import draw_bounding_boxes, draw_grasps

# Cell 2: Load Models
pipeline = SimplePipeline(config)
# ... (load like in testing.ipynb)

# Cell 3: Setup Robot
HOMOGRAPHY_MATRIX = [
    [1.2, 0.01, -150],
    [0.02, 1.3, 200],
    [0.0001, 0.0002, 1]
]  # จากการ calibrate

robot = DobotController(config, HOMOGRAPHY_MATRIX)
robot.connect('COM3')  # หรือ IP
robot.home()

# Cell 4: Single Grasp Test
cap = cv2.VideoCapture(config.CAMERA_ID)
ret, frame = cap.read()
cap.release()

# Process
result = pipeline.process_frame(frame)

# Get best grasp
best_grasp = pipeline.get_best_grasp(result)

if best_grasp:
    print(f"Best grasp quality: {best_grasp.quality:.3f}")
    
    # Visualize
    vis = draw_grasps(frame, [best_grasp])
    cv2.imshow('Grasp to execute', vis)
    cv2.waitKey(0)
    
    # Ask for confirmation
    response = input("Execute this grasp? (y/n): ")
    
    if response.lower() == 'y':
        # Execute!
        robot.execute_grasp(best_grasp, depth_value=0)
    else:
        print("Cancelled")
else:
    print("No grasp found")

# Cell 5: Cleanup
robot.disconnect()
cv2.destroyAllWindows()
```

---

## 7. Troubleshooting

### Robot ไม่เชื่อมต่อ

**ตรวจสอบ:**
- [ ] สาย ethernet เสียบแน่น
- [ ] IP address ถูกต้อง
- [ ] Ping ผ่าน
- [ ] Port ถูกต้อง (default: 29999)
- [ ] Firewall ไม่บล็อก
- [ ] Restart robot และ computer

### Robot จับพลาด (ตำแหน่งผิด)

**สาเหตุที่เป็นไปได้:**
1. **Calibration ไม่ถูกต้อง** → Recalibrate!
2. **Camera เคลื่อนที่** → ตรึงให้แน่น
3. **Workspace limits ผิด** → ตรวจสอบใน config
4. **Depth estimation ผิด** → ปรับ Z offset

### Object Detection จับไม่ได้

- ลด `CONFIDENCE_THRESHOLD` ใน config
- เพิ่มแสง
- ทำให้พื้นหลังต่างสีกับวัตถุ
- ลองวัตถุขนาดใหญ่ขึ้น

### Grasp Quality ต่ำ

- ตรวจสอบแสงและพื้นผิววัตถุ
- ลด `DEPTH_VARIANCE_THRESHOLD`
- เพิ่มจำนวน `GRASP_ORIENTATIONS`

---

## 8. Safety Guidelines ⚠️

### ก่อนเริ่มใช้งาน

- [ขั้นตอนความปลอดภัยหลักการใช้งาน robot ฯลฯ]
- [ ] อ่านคู่มือ Dobot MG400 ทั้งหมด
- [ ] ทำความเข้าใจปุ่ม Emergency Stop
- [ ] ตรวจสอบ workspace ปลอดสิ่งกีดขวาง
- [ ] กำหนด safety limits ใน code
- [ ] มีคนอยู่เฝ้าตลอดเวลาที่ robot ทำงาน

### ระหว่างใช้งาน

✅ **ทำ:**
- เริ่มด้วยความเร็วช้า
- ทดสอบทีละขั้นตอน
- พร้อม Emergency Stop ตลอดเวลา
- ใช้ workspace limits ที่เหมาะสม

❌ **ห้าม:**
- เข้าไปใน workspace ขณะ robot ทำงาน
- ปรับ code ขณะ robot กำลังเคลื่อนที่
- ใช้ความเร็วสูงในการทดสอบครั้งแรก
- ทิ้ง robot ทำงานโดยไม่มีคนเฝ้า

### Emergency Stop

```python
# เพิ่มใน code ทุก loop
try:
    robot.execute_grasp(grasp)
except KeyboardInterrupt:
    robot.emergency_stop()
    print("\n⚠️ Emergency stop!")
except Exception as e:
    robot.emergency_stop()
    print(f"\n⚠️ Error: {e}")
```

---

## 9. Workflow สรุป

### การใช้งานจริงในหน้างาน

```
1. เตรียมอุปกรณ์
   ├─ ติดตั้ง camera
   ├─ เชื่อมต่อ robot
   └─ ตรวจสอบ workspace

2. Calibrate (ครั้งแรก หรือเมื่อ camera เคลื่อนที่)
   ├─ วาง checkerboard
   ├─ ถ่ายภาพหลายมุม
   ├─ คำนวณ homography
   └─ ทดสอบ accuracy

3. Load System
   ├─ เปิด notebook
   ├─ Load models
   ├─ Connect robot
   └─ Home robot

4. ทดสอบ Single Grasp
   ├─ Capture frame
   ├─ Detect objects & grasps
   ├─ แสดงผล และ confirm
   └─ Execute (ถ้า OK)

5. Production Mode
   ├─ Loop: Capture → Detect → Grasp
   ├─ Monitor performance
   └─ Adjust parameters ถ้าจำเป็น

6. Shutdown
   ├─ Home robot
   ├─ Disconnect
   └─ Save logs/results
```

---

## 10. Performance Tips

### เพิ่มความเร็ว

```python
# ใน config.py

# ใช้ GPU ถ้ามี
DEVICE = 'cuda'

# ลดความละเอียด camera (ถ้ายอมได้)
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# ลด orientations (ถ้าพอ)
GRASP_ORIENTATIONS = [0, 90]  # แค่ 2 มุม
```

### เพิ่มความแม่นยำ

```python
# เพิ่มความละเอียด
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# เพิ่ม orientations
GRASP_ORIENTATIONS = [0, 30, 45, 60, 90, 120, 135, 150]

# Strict quality threshold
DEPTH_VARIANCE_THRESHOLD = 0.05
```

---

## สรุป Checklist ก่อนใช้งานจริง

- [ ] Hardware setup completed
- [ ] Software installed
- [ ] Camera calibrated
- [ ] Robot connected & tested
- [ ] Workspace limits configured
- [ ] Safety guidelines understood
- [ ] Single grasp test successful
- [ ] Emergency stop tested
- [ ] Team briefed on operation

---

**หมายเหตุ:** เอกสารนี้เป็นแนวทางทั่วไป ในการใช้งานจริงอาจต้องปรับแต่งตามสภาพแวดล้อมและความต้องการเฉพาะ

**เวอร์ชัน:** 1.0  
**อัพเดทล่าสุด:** 2025-01-25
