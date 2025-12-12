# LIDAR Grasp Detection System v13
## รายงานสรุปโครงการ

---

# สารบัญ

1. บทนำ
2. ภาพรวมระบบ
3. Hardware ที่ใช้
4. หลักการทำงาน
5. ขั้นตอนการทำงาน
6. Configuration และ Calibration
7. Code Architecture
8. ผลลัพธ์และประสิทธิภาพ
9. ข้อดีและข้อจำกัด
10. การพัฒนาต่อยอด

---

# 1. บทนำ

## 1.1 วัตถุประสงค์
พัฒนาระบบหยิบจับวัตถุอัตโนมัติ (Robotic Grasping) สำหรับหุ่นยนต์ Dobot MG400 
โดยใช้ LIDAR วัดความสูงจริง และ Computer Vision ตรวจจับตำแหน่งวัตถุ

## 1.2 เป้าหมาย
- หยิบจับวัตถุได้แม่นยำ (error < 5mm)
- ทำงานได้เร็ว (< 100ms ต่อ frame)
- ไม่พึ่งพา Deep Learning Model (ลด dependency)
- ใช้ได้กับวัตถุทุกสี ทุกขนาด

## 1.3 ความแตกต่างจาก Version ก่อน
| Version | Object Detection | Depth/Height | Grasp Selection |
|---------|------------------|--------------|-----------------|
| v9-v10 | YOLOv8 (AI) | Depth Anything V2 | Rule-based |
| v11-v12 | YOLOv8 (AI) | LIDAR | Rule-based |
| **v13** | **Color+Edge (CV)** | **LIDAR** | **PCA** |

---

# 2. ภาพรวมระบบ

## 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LIDAR GRASP SYSTEM v13                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    CAMERA     │    │    LIDAR      │    │    ROBOT      │
│   (USB Cam)   │    │  (TF-Luna)    │    │  (MG400)      │
│               │    │               │    │               │
│  - Detection  │    │  - Height     │    │  - MovJ       │
│  - Tracking   │    │  - Distance   │    │  - Gripper    │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     ▲
        ▼                     ▼                     │
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Color+   │→ │  PCA     │→ │  LIDAR   │→ │  Robot   │    │
│  │ Edge     │  │  Grasp   │  │  Height  │  │  Control │    │
│  │ Detect   │  │  Select  │  │  Calc    │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 Data Flow

1. **Camera** → จับภาพ frame (640x480)
2. **Detection** → หาวัตถุด้วย Color+Edge
3. **PCA** → คำนวณมุมและขนาดจับ
4. **User Click** → เลือกวัตถุ
5. **LIDAR** → วัดความสูงจริง
6. **Z Calculation** → คำนวณความสูงหยิบ
7. **Robot** → เคลื่อนที่และหยิบ

---

# 3. Hardware ที่ใช้

## 3.1 Dobot MG400
- **Type**: Desktop Collaborative Robot
- **DOF**: 4-axis (SCARA)
- **Payload**: 750g
- **Reach**: 440mm
- **Repeatability**: ±0.05mm
- **Communication**: TCP/IP (Port 29999)
- **IP Address**: 192.168.1.6

## 3.2 TF-Luna LIDAR
- **Type**: Time-of-Flight (ToF)
- **Range**: 0.2m - 8m
- **Accuracy**: ±2cm @ 0.2-3m
- **Frame Rate**: 250 Hz
- **Interface**: UART
- **Connected via**: ESP32

## 3.3 ESP32 Controller
- **Function**: Gripper + LIDAR control
- **COM Port**: COM9
- **Baudrate**: 115200
- **Commands**:
  - `G<angle>` - Set gripper angle
  - `L` - Read LIDAR distance

## 3.4 Servo Gripper
- **Servo**: MG996R or similar
- **Range**: 22° - 96°
- **Width**: 0mm - 54mm
- **Response Time**: ~300ms

## 3.5 USB Camera
- **Resolution**: 640x480
- **FPS**: 30
- **Camera ID**: 2 (adjustable)

---

# 4. หลักการทำงาน

## 4.1 Object Detection (Color + Edge)

### 4.1.1 Saturation-based Detection
```python
# Convert to HSV
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)

# Threshold on saturation (colored objects)
_, sat_mask = cv2.threshold(s, 50, 255, cv2.THRESH_BINARY)

# Detect dark objects
_, dark_mask = cv2.threshold(v, 80, 255, cv2.THRESH_BINARY_INV)

# Combine
combined_mask = cv2.bitwise_or(sat_mask, dark_mask)
```

**หลักการ**: 
- วัตถุที่มีสีจะมีค่า Saturation สูง (> 50)
- วัตถุสีดำจะมีค่า Value ต่ำ (< 80)
- รวมทั้ง 2 mask เพื่อจับได้ทุกสี

### 4.1.2 Edge Detection (Fallback)
```python
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blur, 50, 150)
```

**ใช้เมื่อ**: Color detection ไม่เจอวัตถุ (เช่น วัตถุสีเทา)

### 4.1.3 Contour Processing
```python
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                cv2.CHAIN_APPROX_SIMPLE)
for cnt in contours:
    area = cv2.contourArea(cnt)
    if MIN_OBJECT_AREA < area < MAX_OBJECT_AREA:
        hull = cv2.convexHull(cnt)
        rect = cv2.minAreaRect(hull)
```

---

## 4.2 PCA Grasp Selection

### 4.2.1 Principal Component Analysis
```python
# Get contour points
pts = contour.reshape(-1, 2).astype(np.float64)
mean = np.mean(pts, axis=0)
pts_centered = pts - mean

# Calculate covariance and eigenvectors
cov = np.cov(pts_centered.T)
eigenvalues, eigenvectors = np.linalg.eig(cov)

# Sort by eigenvalue (descending)
idx = np.argsort(eigenvalues)[::-1]
major = eigenvectors[:, idx[0]]  # longest axis
minor = eigenvectors[:, idx[1]]  # shortest axis
```

### 4.2.2 Grasp Calculation
```python
# Grasp angle = perpendicular to major axis
angle = np.degrees(np.arctan2(major[1], major[0]))
grasp_angle = angle + 90  # perpendicular

# Grasp width = object width along minor axis
proj = np.dot(pts_centered, minor)
width_mm = (np.max(proj) - np.min(proj)) / PIXELS_PER_MM
```

**หลักการ**: จับวัตถุจากด้านแคบ (ตั้งฉากกับแกนยาว)

---

## 4.3 LIDAR Height Calculation

### 4.3.1 LIDAR Reading
```python
def read_lidar(samples=5):
    readings = []
    for _ in range(samples):
        serial.write(b'L\n')
        response = serial.readline()  # "LIDAR:xxx"
        dist = int(response.split(":")[1])
        readings.append(dist)
    return np.median(readings)
```

### 4.3.2 Z Calculation Formula
```python
# Step 1: Base Z
z_base = Z_MEASURE - lidar_reading + LIDAR_PHYSICAL_OFFSET

# Step 2: Apply correction
z_corrected = z_base + LIDAR_CORRECTION

# Step 3: Height-based correction
estimated_height = Z_FLOOR - z_corrected + (Z_MEASURE - Z_FLOOR)
height_correction = estimated_height * HEIGHT_CORRECTION_FACTOR
z_grasp = z_corrected - height_correction

# Step 4: Safety limit
z_grasp = max(Z_FLOOR, z_grasp)
```

**ตัวอย่างการคำนวณ**:
```
Z_MEASURE = 120
lidar_reading = 100
LIDAR_PHYSICAL_OFFSET = 60
LIDAR_CORRECTION = -21

z_base = 120 - 100 + 60 = 80
z_corrected = 80 + (-21) = 59
height_correction = 143 * 0.115 = 16.4
z_grasp = 59 - 16.4 = 42.6
```

---

## 4.4 Coordinate Transformation

### 4.4.1 Homography Matrix
```python
# 4 corresponding points
pixel_pts = [(u1,v1), (u2,v2), (u3,v3), (u4,v4)]
robot_pts = [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]

H, _ = cv2.findHomography(pixel_pts, robot_pts)
np.save('homography_matrix.npy', H)
```

### 4.4.2 Pixel to Robot
```python
def pixel_to_robot(u, v):
    pt = np.array([u, v, 1], dtype=np.float32)
    res = np.dot(H, pt)
    return res[0]/res[2], res[1]/res[2]
```

---

# 5. ขั้นตอนการทำงาน (Pick Sequence)

## 5.1 Pre-Pick
1. Robot Home Position
2. Open Gripper (max width)
3. Wait for camera detection

## 5.2 Detection Phase
4. Camera captures frame
5. Color+Edge detection
6. PCA calculates grasp points
7. Display on screen
8. User clicks to select object

## 5.3 LIDAR Measurement
9. Move LIDAR above object (Z_MEASURE)
10. Read LIDAR distance (100 samples)
11. Calculate Z_GRASP

## 5.4 Pick Phase
12. Move gripper above object (Z_MEASURE)
13. Rotate to grasp angle
14. Lower to Z_GRASP
15. Close gripper
16. Lift up (+50mm)

## 5.5 Place Phase
17. Move to DROP_POS
18. Open gripper
19. Lift up
20. Return to Home

---

# 6. Configuration และ Calibration

## 6.1 Camera Calibration

### PIXELS_PER_MM
```python
PIXELS_PER_MM = 2.7703  # pixels per millimeter
```
**วิธี Calibrate**: วัดระยะ pixel ของวัตถุที่รู้ขนาดจริง

### HOMOGRAPHY_MATRIX
```python
HOMOGRAPHY_MATRIX = np.load('homography_matrix.npy')
```
**วิธี Calibrate**: 4-point calibration (วางจุดอ้างอิง 4 จุด)

## 6.2 Robot Calibration

### Z_FLOOR
```python
Z_FLOOR = -64  # mm (Z when gripper touches floor)
```
**วิธี Calibrate**: ใช้ Teach Mode ลง gripper แตะพื้น

### ROBOT_R_OFFSET
```python
ROBOT_R_OFFSET = -25.55  # degrees
```
**วิธี Calibrate**: ปรับจนกว่า gripper จะหมุนตรงกับ object

## 6.3 LIDAR Calibration

### LIDAR XY Offset
```python
LIDAR_X_OFFSET = 25.08  # mm
LIDAR_Y_OFFSET = 20.71  # mm
```
**วิธี Calibrate**: วัดระยะจาก gripper center ไป LIDAR

### LIDAR Physical Offset
```python
LIDAR_PHYSICAL_OFFSET = 60  # mm
```
**วิธี Calibrate**: อ่านค่า LIDAR เมื่อ gripper แตะพื้น

### LIDAR Correction
```python
LIDAR_CORRECTION = -21  # mm
```
**วิธี Calibrate**: ทดสอบกับวัตถุที่รู้ความสูง

### Height Correction Factor
```python
HEIGHT_CORRECTION_FACTOR = 0.115  # 11.5%
```
**วิธี Calibrate**: ปรับจากการทดสอบ pick จริง

## 6.4 Gripper Calibration

### Angle-Width Lookup Table
```python
CALIB_ANGLES = [22, 30, 40, 50, 60, 70, 80, 90, 96]
CALIB_WIDTHS = [54, 52, 48, 40, 32, 23, 12,  3,  0]
```
**วิธี Calibrate**: ส่ง angle แต่ละค่า แล้ววัดความกว้างจริง

---

# 7. Code Architecture

## 7.1 Classes

### SmartGripperController
```python
class SmartGripperController:
    - connect()
    - disconnect()
    - send_command(cmd)
    - mm_to_angle(width_mm)
    - open_for_object(width_mm)
    - grip_object(width_mm)
    - release()
    - read_lidar(samples)
```

### DobotControllerTCP
```python
class DobotControllerTCP:
    - connect(ip)
    - send_command(cmd)
    - home()
    - move_to(x, y, z, r)
    - move_to_and_wait(x, y, z, r, wait)
    - joint_move(j1, j2, j3, j4)
    - pixel_to_robot(u, v)
    - camera_angle_to_robot_r(camera_angle)
```

### ObjectDetectorV13
```python
class ObjectDetectorV13:
    - detect(frame)
    - _detect_by_saturation(frame)
    - _detect_by_edge(frame)
    - _contour_to_object(contour, method)
    - _remove_duplicates(objects)
```

### PCAGraspSelector
```python
class PCAGraspSelector:
    - analyze_object(obj)
    - _fallback(obj)
    - _normalize(angle)
```

## 7.2 Main Functions

### pick_with_lidar_v13()
Main pick sequence function:
1. Calculate robot coordinates
2. Open gripper
3. Move LIDAR above object
4. Read LIDAR and calculate Z
5. Move gripper and rotate
6. Lower and grip
7. Lift and place

### mouse_callback()
Handle mouse clicks for object selection

### draw_grasps()
Visualize grasp points on frame

---

# 8. ผลลัพธ์และประสิทธิภาพ

## 8.1 Performance

| Metric | Value |
|--------|-------|
| Detection Speed | ~30ms |
| LIDAR Reading | ~50ms (100 samples) |
| Total Cycle Time | ~15-20 seconds |
| Position Accuracy | ±3-5mm |
| Height Accuracy | ±2mm |
| Success Rate | ~90%+ |

## 8.2 Limitations

- ไม่รองรับวัตถุโปร่งใส
- ต้องมีแสงสม่ำเสมอ
- วัตถุต้องมี contrast กับพื้นหลัง
- Gripper width จำกัดที่ 54mm

---

# 9. ข้อดีและข้อจำกัด

## 9.1 ข้อดี

| ข้อดี | รายละเอียด |
|-------|------------|
| **ไม่ใช้ AI/ML** | ไม่ต้อง GPU, โหลดเร็ว |
| **LIDAR แม่นยำ** | วัดความสูงจริง ไม่ประมาณ |
| **Self-contained** | ทุกอย่างใน notebook เดียว |
| **Calibrate ง่าย** | มี calibration notebook |
| **Debug ง่าย** | ไม่มี black box |

## 9.2 ข้อจำกัด

| ข้อจำกัด | แนวทางแก้ไข |
|----------|-------------|
| ไม่รู้จัก object class | ใช้ YOLO ถ้าต้องการ |
| LIDAR ต้องอยู่ใกล้ | ใช้ LIDAR range ไกลกว่า |
| Gripper width จำกัด | เปลี่ยน gripper |

---

# 10. การพัฒนาต่อยอด

## 10.1 Short-term
- [ ] เพิ่ม object rotation tracking
- [ ] เพิ่ม multiple object picking
- [ ] เพิ่ม GUI for parameter tuning

## 10.2 Long-term
- [ ] Integration with conveyor belt
- [ ] 3D object reconstruction
- [ ] AI-assisted object classification

---

# ภาคผนวก

## A. ESP32 Code

```cpp
// Gripper command: G<angle>
if (cmd.startsWith("G")) {
  int angle = cmd.substring(1).toInt();
  servo.write(angle);
}

// LIDAR command: L
if (cmd == "L") {
  int dist = lidar.getDistance();
  Serial.println("LIDAR:" + String(dist));
}
```

## B. Dependencies

```
opencv-python>=4.5.0
numpy>=1.20.0
pyserial>=3.5
```

## C. File List

| File | Description |
|------|-------------|
| 13_sc_best_lidar_grasp_v13_new.ipynb | Main notebook |
| calibrate_for_v13.ipynb | Calibration |
| homography_matrix.npy | Calibration data |
| README.md | Documentation |

---

**Document Version**: 1.0  
**Created**: December 2025  
**System Version**: v13 (LIDAR Grasp - No AI)
