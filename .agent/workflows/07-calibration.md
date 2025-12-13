# 📐 Calibration

## 📌 Overview

ขั้นตอนการ Calibrate ระบบก่อนใช้งาน Auto-Pick

---

## 🔧 Calibration Components

| # | Component | File/Output | Purpose |
|---|-----------|-------------|---------|
| 1 | Homography Matrix | `homography_matrix.npy` | Pixel → Robot coordinates |
| 2 | Gripper Width | Code constants | Servo angle → Width mapping |
| 3 | LIDAR Offset | Code constants | Height measurement accuracy |
| 4 | Robot R Offset | `ROBOT_R_OFFSET` | Camera-Robot angle alignment |

---

## 1️⃣ Homography Calibration

### Purpose
แปลงพิกัดจากกล้อง (pixels) ไปเป็นพิกัดหุ่นยนต์ (mm)

### Method: 4-Point Calibration

```
┌─────────────────────────────────────────────────────────────────┐
│                  4-POINT CALIBRATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     Camera View (Pixels)         Robot Workspace (mm)           │
│     ────────────────────         ────────────────────           │
│                                                                 │
│     A───────────────B            A───────────────B              │
│     │               │            │               │              │
│     │   ┌───────┐   │            │   ┌───────┐   │              │
│     │   │Workspace  │            │   │Workspace  │              │
│     │   └───────┘   │            │   └───────┘   │              │
│     │               │            │               │              │
│     D───────────────C            D───────────────C              │
│                                                                 │
│     (u_a, v_a) → (x_a, y_a)                                     │
│     (u_b, v_b) → (x_b, y_b)                                     │
│     (u_c, v_c) → (x_c, y_c)                                     │
│     (u_d, v_d) → (x_d, y_d)                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Steps

1. **Place 4 markers** at workspace corners

2. **Record pixel coordinates** (click on camera image)
   ```python
   pixel_points = [
       (120, 80),   # Point A
       (520, 85),   # Point B
       (525, 400),  # Point C
       (115, 395),  # Point D
   ]
   ```

3. **Record robot coordinates** (from Dobot Studio)
   ```python
   robot_points = [
       (-50.0, 100.0),   # Point A
       (150.0, 100.0),   # Point B
       (150.0, -50.0),   # Point C
       (-50.0, -50.0),   # Point D
   ]
   ```

4. **Calculate Homography**
   ```python
   H, status = cv2.findHomography(
       np.array(pixel_points), 
       np.array(robot_points)
   )
   np.save('homography_matrix.npy', H)
   ```

### Verification
```python
# Test transformation
test_pixel = (320, 240)  # Center of camera
robot_x, robot_y = robot.pixel_to_robot(*test_pixel)
print(f"Pixel {test_pixel} → Robot ({robot_x:.1f}, {robot_y:.1f})")

# Move robot to verify
robot.move_to(robot_x, robot_y, Z_MEASURE, 0)
# Check if robot is at expected position
```

---

## 2️⃣ Gripper Width Calibration

### Purpose
สร้าง mapping ระหว่างมุม servo กับความกว้าง gripper

### Method: Physical Measurement

```
┌─────────────────────────────────────────────────────────────────┐
│               GRIPPER CALIBRATION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Step 1: Set servo to angle                                    │
│   ──────────────────────────                                    │
│   gripper.send_command('G22')                                   │
│                                                                 │
│   Step 2: Measure with ruler                                    │
│   ──────────────────────────                                    │
│        ═══      ═══                                             │
│          ╲      ╱                                               │
│           ╲    ╱                                                │
│            ╲  ╱                                                 │
│            ◀──▶                                                 │
│           54mm (measured)                                       │
│                                                                 │
│   Step 3: Record in table                                       │
│   ──────────────────────────                                    │
│   Angle → Width                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Calibration Data
```python
CALIB_ANGLES = [22, 30, 40, 50, 60, 70, 80, 90, 96]
CALIB_WIDTHS = [54.0, 52.0, 48.0, 40.0, 32.0, 23.0, 12.0, 3.0, 0.0]
```

### Calibration Curve
```
Width (mm)
   60 ┤
   54 ├─────●                        
   52 │      ●                       
   48 │         ●                    
   40 │             ●                
   32 │                 ●            
   23 │                     ●        
   12 │                         ●    
    3 │                            ●
    0 ├────────────────────────────●─
      22   30   40   50   60   70   80   90  96
                              Angle (°)
```

---

## 3️⃣ LIDAR Offset Calibration

### Parameters to Calibrate

| Parameter | Description | How to Measure |
|-----------|-------------|----------------|
| `LIDAR_PHYSICAL_OFFSET` | Distance from LIDAR to gripper tip | Physical measurement |
| `LIDAR_X_OFFSET` | X offset from gripper center | Trial and error |
| `LIDAR_Y_OFFSET` | Y offset from gripper center | Trial and error |
| `LIDAR_CORRECTION` | Systematic error correction | Comparison test |

### Step 1: Physical Offset
```
     Gripper
    ┌─────┴─────┐
    │  LIDAR ◎  │ ← LIDAR sensor
    │           │
    │   ╔═══╗   │
    │   ║   ║   │
    │   ╚═══╝   │
    └───────────┘
         │
         ▼
    Gripper Tip
    
    Measure: LIDAR to Tip = 60mm (LIDAR_PHYSICAL_OFFSET)
```

### Step 2: X/Y Offset
```python
# 1. Place object at known position
# 2. Detect object center
# 3. Move LIDAR above object
# 4. Adjust offsets until LIDAR reads over object center

LIDAR_X_OFFSET = 25.08  # Adjust until aligned
LIDAR_Y_OFFSET = 20.71  # Adjust until aligned
```

### Step 3: Correction Factor
```python
# 1. Place object of KNOWN height
# 2. Read LIDAR distance
# 3. Calculate expected vs actual

# Known: Object height = 30mm on Z_FLOOR = -64
# Expected Z = -64 + 30 = -34

# LIDAR reads 156mm at Z_MEASURE = 120
# Calculated: z = 120 - 156 + 60 = 24 (wrong!)

# Apply correction: LIDAR_CORRECTION = -21
# New: z = 120 - 156 + 60 + (-21) = 3 (closer!)

# Fine-tune HEIGHT_CORRECTION_FACTOR for final accuracy
```

---

## 4️⃣ Robot Angle Offset Calibration

### Purpose
แก้ไขความต่างของทิศทางระหว่างกล้องกับหุ่นยนต์

### Method
```python
# 1. Place elongated object (e.g., pen) at known angle
# 2. Camera detects angle (e.g., camera_angle = 45°)
# 3. Robot grips with robot_r = 0
# 4. Check if gripper aligned with object

# If not aligned:
# robot_r = ROBOT_R_OFFSET - camera_angle

# Adjust ROBOT_R_OFFSET until aligned
ROBOT_R_OFFSET = -25.55  # Degrees
```

### Visual Check
```
   Camera View        Robot View (Top)
   
       45°                  45°
        ╲                    ╲
         ╲  PEN              ╲  PEN
          ╲                    ╲
                         ═══════════
                           Gripper
                           
   If gripper not parallel → adjust ROBOT_R_OFFSET
```

---

## 📋 Calibration Checklist

```
□ 1. Homography Matrix
   □ Place 4 markers at corners
   □ Record pixel coordinates
   □ Record robot coordinates  
   □ Calculate and save matrix
   □ Verify with test points

□ 2. Gripper Width
   □ Test angles: 22, 30, 40, 50, 60, 70, 80, 90, 96
   □ Measure width at each angle
   □ Update CALIB_ANGLES and CALIB_WIDTHS

□ 3. LIDAR Offset
   □ Measure physical offset (LIDAR to tip)
   □ Calibrate X/Y offsets
   □ Verify with known-height object
   □ Tune LIDAR_CORRECTION
   □ Tune HEIGHT_CORRECTION_FACTOR

□ 4. Robot Angle Offset
   □ Test with elongated object
   □ Adjust ROBOT_R_OFFSET until aligned
```

---

## 🔧 Quick Re-calibration

If environment changes (camera moved, robot repositioned):

### Minimum Steps
1. **Re-do Homography** (if camera moved)
2. **Verify LIDAR readings** (if mounting changed)
3. **Check angle offset** (if camera rotated)

### Test Command
```python
# Quick verification test
test_points = [(200, 150), (400, 150), (300, 300)]
for px, py in test_points:
    rx, ry = robot.pixel_to_robot(px, py)
    print(f"Pixel ({px}, {py}) → Robot ({rx:.1f}, {ry:.1f})")
    robot.move_to(rx, ry, Z_MEASURE, 0)
    input("Check position and press Enter...")
```
