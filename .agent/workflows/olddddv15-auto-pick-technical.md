---
description: Technical workflow for v15 Auto-Pick robotic grasping system
---

# 🤖 v15 Auto-Pick System - Technical Workflow

## 📋 System Overview

ระบบหยิบวัตถุอัตโนมัติโดยใช้ Dobot MG400 ร่วมกับ Computer Vision, LIDAR sensor และ Servo Gripper

---

## 🔧 Hardware Components

| Component | Model/Spec | Connection |
|-----------|------------|------------|
| Robot Arm | Dobot MG400 | TCP/IP `192.168.1.6:29999` |
| Camera | USB Webcam | `CAMERA_ID = 2` |
| Gripper+LIDAR | ESP32 + Servo + VL53L0X | Serial `COM9` @ 115200 baud |
| Homography | Pre-calibrated matrix | `homography_matrix.npy` |

---

## 🔄 State Machine Architecture

```
┌─────────┐    Object Found    ┌──────────┐
│  IDLE   │ ───────────────────▶│ DETECTED │
└─────────┘                     └────┬─────┘
     ▲                               │ 4 seconds stable
     │                               ▼
     │ Reset/Object Lost       ┌──────────┐
     │◀────────────────────────│  STABLE  │
     │                         └────┬─────┘
     │                               │ Immediate
     │                               ▼
     │                         ┌───────────┐
     │◀────────────────────────│ COUNTDOWN │──── 3 seconds ────┐
     │   Object Moved          └───────────┘                   │
     │                                                         ▼
     │                         ┌──────────┐              ┌─────────┐
     └─────────────────────────│ COOLDOWN │◀─────────────│ PICKING │
               3 seconds       └──────────┘              └─────────┘
```

---

## 📐 Coordinate Systems

### 1. Camera (Pixel) Space
- Origin: Top-left of frame
- Unit: Pixels
- Resolution: 640x480

### 2. Robot (World) Space
- Origin: Robot base
- Unit: Millimeters
- Frame: User(1), Tool(1)

### 3. Transformation
```python
# Homography: Pixel → Robot
pt = np.array([u, v, 1], dtype=np.float32)
res = np.dot(HOMOGRAPHY_MATRIX, pt)
robot_x, robot_y = res[0]/res[2], res[1]/res[2]

# Angle: Camera → Robot
robot_r = ROBOT_R_OFFSET - camera_angle  # ROBOT_R_OFFSET = -25.55°
```

---

## 🎯 Object Detection Pipeline

### Step 1: Color Segmentation (HSV)
```python
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)

# Saturated objects (colored)
_, sat_mask = cv2.threshold(s, 50, 255, cv2.THRESH_BINARY)

# Dark objects
_, dark_mask = cv2.threshold(v, 80, 255, cv2.THRESH_BINARY_INV)

combined_mask = cv2.bitwise_or(sat_mask, dark_mask)
```

### Step 2: Morphological Cleanup
```python
kernel = np.ones((5, 5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # Remove noise
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Fill holes
```

### Step 3: Contour Analysis
```python
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

# Filter by area
MIN_OBJECT_AREA = 800
MAX_OBJECT_AREA = 50000
```

### Step 4: Donut Detection
```python
# Detect inner holes (child contours)
hole_ratio = hole_area / outer_area

# Circularity check
circularity = 4 * np.pi * area / (perimeter ** 2)

# Donut criteria
is_donut = (0.1 <= hole_ratio <= 0.7) and (circularity >= 0.5)
```

---

## 🤏 Grasp Analysis

### Solid Objects (PCA Method)
```python
# Compute principal axes
pts = contour.reshape(-1, 2).astype(np.float64)
mean = np.mean(pts, axis=0)
cov = np.cov((pts - mean).T)
eigenvalues, eigenvectors = np.linalg.eig(cov)

# Major/Minor axis
major = eigenvectors[:, np.argmax(eigenvalues)]
minor = eigenvectors[:, np.argmin(eigenvalues)]

# Grasp across minor axis (narrower dimension)
grasp_angle = np.degrees(np.arctan2(major[1], major[0])) + 90
grip_width = projection_along_minor / PIXELS_PER_MM
```

### Donut Objects (Radial Method)
```python
# Ring thickness
ring_thickness_px = outer_radius - hole_radius
ring_thickness_mm = ring_thickness_px / PIXELS_PER_MM

# 4 grasp positions (0°, 90°, 180°, 270°)
grasp_radius = (outer_radius + hole_radius) / 2
grasp_point = center + grasp_radius * [cos(angle), sin(angle)]

# Grasp angle = radial direction (pointing toward center)
```

---

## 📏 Height Measurement (LIDAR)

### LIDAR Reading
```python
# ESP32 command: 'L' → Response: 'LIDAR:XXX'
readings = []
for _ in range(100):  # 100 samples for accuracy
    serial.write(b'L\n')
    response = serial.readline()  # "LIDAR:185"
    readings.append(int(response.split(':')[1]))

lidar_dist = np.median(readings)
```

### Z Calculation
```python
# Physical setup
Z_MEASURE = 120       # Height where LIDAR reads
Z_FLOOR = -64         # Ground level
LIDAR_PHYSICAL_OFFSET = 60
LIDAR_CORRECTION = -21

# Calculate grasp Z
z_base = Z_MEASURE - lidar_dist + LIDAR_PHYSICAL_OFFSET + LIDAR_CORRECTION
estimated_height = max(0, Z_FLOOR - z_base + (Z_MEASURE - Z_FLOOR))
z_grasp = z_base - estimated_height * HEIGHT_CORRECTION_FACTOR  # 0.115

z_grasp = max(Z_FLOOR, z_grasp)  # Clamp to floor
```

---

## 🦾 Gripper Control

### Width-to-Angle Mapping
```python
CALIB_ANGLES = [22, 30, 40, 50, 60, 70, 80, 90, 96]  # Servo degrees
CALIB_WIDTHS = [54, 52, 48, 40, 32, 23, 12, 3, 0]    # mm

angle = np.interp(width_mm, CALIB_WIDTHS[::-1], CALIB_ANGLES[::-1])
serial.write(f'G{angle}\n'.encode())  # ESP32 command
```

### Gripper Modes
| Mode | Pre-open Width | Use Case |
|------|----------------|----------|
| Solid | `GRIPPER_MAX_WIDTH_MM` (54mm) | Full open |
| Donut | `ring_thickness + 15 + 5mm margin` | Precise fit |

---

## 🔄 Pick Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SAFE POSITION                                                │
│    robot.joint_move(0, 0, 0, 0)                                │
├─────────────────────────────────────────────────────────────────┤
│ 2. GRIPPER PRE-OPEN                                             │
│    Donut: open_to_width(ring_thickness + margin)               │
│    Solid: open_for_object(54mm)                                │
├─────────────────────────────────────────────────────────────────┤
│ 3. LIDAR MEASUREMENT                                            │
│    Move to (lidar_x + 25.08, lidar_y + 20.71, Z_MEASURE=120)   │
│    Read LIDAR 100 samples → Calculate z_grasp                  │
├─────────────────────────────────────────────────────────────────┤
│ 4. APPROACH                                                     │
│    Move to (gripper_x, gripper_y, Z_MEASURE)                   │
│    Rotate to final_r = ROBOT_R_OFFSET - camera_angle           │
├─────────────────────────────────────────────────────────────────┤
│ 5. DESCEND                                                      │
│    Move to (gripper_x, gripper_y, z_grasp)                     │
├─────────────────────────────────────────────────────────────────┤
│ 6. GRIP                                                         │
│    grip_object(width - 8.5mm)  # Squeeze margin                │
│    Wait 4 seconds                                              │
├─────────────────────────────────────────────────────────────────┤
│ 7. LIFT                                                         │
│    Move to z_grasp + 50mm                                      │
├─────────────────────────────────────────────────────────────────┤
│ 8. DROP                                                         │
│    Move to DROP_POS (169.71, 58.01, -17.07, 13.78)            │
│    gripper.release()                                           │
├─────────────────────────────────────────────────────────────────┤
│ 9. RETURN HOME                                                  │
│    robot.home() → (-253.07, 115.17, -17.07, -62.78)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⏱️ Auto-Pick Timing

| Phase | Duration | Trigger |
|-------|----------|---------|
| Detection | Instant | Object appears in frame |
| Stability Check | 4.0s | Object must not move > 20px or change area > 15% |
| Countdown | 3.0s | Visual countdown with progress ring |
| Picking | ~30s | Full pick sequence |
| Cooldown | 3.0s | Prevent immediate re-detection |

### Stability Check Logic
```python
def is_same_object(self, obj):
    dx = abs(obj['center'][0] - self.tracked_center[0])
    dy = abs(obj['center'][1] - self.tracked_center[1])
    area_diff = abs(obj['area'] - self.tracked_area) / self.tracked_area
    
    return (dx < 20) and (dy < 20) and (area_diff < 0.15)
```

---

## 📡 Communication Protocols

### Dobot TCP/IP Commands
```python
# Dashboard port: 29999
sock.connect(('192.168.1.6', 29999))

sock.send("ClearError()\n")
sock.send("EnableRobot()\n")
sock.send("User(1)\n")
sock.send("Tool(1)\n")
sock.send("SpeedFactor(50)\n")
sock.send("MovJ(x, y, z, r)\n")
sock.send("JointMovJ(j1, j2, j3, j4)\n")
```

### ESP32 Serial Commands
```python
# Gripper control
serial.write(b'G45\n')  # Set servo to 45°

# LIDAR reading
serial.write(b'L\n')    # Returns "LIDAR:185"
```

---

## 🖥️ Visual Feedback

### Progress Ring Drawing
```python
def draw_progress_ring(display, center, progress, radius=50):
    start_angle = -90  # Start from top
    end_angle = start_angle + int(360 * progress)
    cv2.ellipse(display, center, (radius, radius), 0, 
                start_angle, end_angle, color, thickness=8)
```

### State Colors
```python
STATE_COLORS = {
    IDLE:      (100, 100, 100),  # Gray
    DETECTED:  (0, 200, 255),    # Orange
    STABLE:    (255, 200, 0),    # Cyan
    COUNTDOWN: (0, 128, 255),    # Orange-Red
    PICKING:   (0, 0, 255),      # Red
    COOLDOWN:  (128, 128, 128),  # Gray
}
```

---

## ⚠️ Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| LIDAR fail | `readings == []` | Return to home |
| Object lost | `target is None` | Reset state machine |
| Object moved | `!is_same_object()` | Restart detection |
| Grasp fail | Manual observation | Manual intervention |

---

## 📁 File Structure

```
this_one_is_main_v13/
├── 15_auto_pick_v15.ipynb     # Main notebook
├── 15_auto_pick_v15.py        # Python source backup
├── 14.1_best_use_donut_grasp_v14_1.ipynb  # Previous version
├── homography_matrix.npy      # Calibration data
└── ...
```
