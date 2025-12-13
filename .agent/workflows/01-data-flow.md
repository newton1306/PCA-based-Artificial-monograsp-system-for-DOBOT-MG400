# 📊 Data Flow

## 📌 Overview

การไหลของข้อมูลในระบบ Auto-Pick v15

---

## 🔄 Main Data Flow

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│  INPUT   │───▶│ PROCESSING│───▶│ PLANNING │───▶│  OUTPUT  │
│ Camera   │    │ Detection │    │ Grasp    │    │ Robot    │
│ LIDAR    │    │ Tracking  │    │ Selection│    │ Gripper  │
└──────────┘    └───────────┘    └──────────┘    └──────────┘
```

---

## 📸 Image Processing Flow

```
RAW FRAME (BGR)
     │
     ▼
HSV CONVERSION ────▶ Split: H, S, V
     │
     ├───▶ Saturation Mask (S > 50)
     │
     └───▶ Dark Mask (V < 80)
              │
              ▼
         OR Combine
              │
              ▼
      Morphology (Open/Close)
              │
              ▼
       findContours
              │
              ▼
       Object List
```

---

## 📦 Data Structures

### Object
```python
object = {
    'bbox': (x, y, w, h),      # Bounding box
    'center': (cx, cy),         # Center (pixels)
    'area': float,              # Area (pixels²)
    'contour': np.array,        # Shape points
    'is_donut': bool,           # Classification
    'hole_ratio': float         # Hole/Total ratio
}
```

### Grasp
```python
grasp = {
    'center': (gx, gy),         # Grasp point
    'lidar_point': (lx, ly),    # LIDAR point
    'width_mm': float,          # Grip width (mm)
    'camera_angle': float,      # Angle (degrees)
    'type': str,                # 'PCA-Solid'/'Donut-Edge'
    'is_donut_grasp': bool
}
```

---

## 🔄 State Machine Flow

```
detected_objects ──▶ IDLE ──▶ DETECTED ──▶ STABLE ──▶ COUNTDOWN ──▶ PICKING
                      │         │            │           │
                      └─────────┴────────────┴───────────┘
                              (reset on object lost)
```

| State | Input | Output |
|-------|-------|--------|
| IDLE | objects[] | "Scanning..." |
| DETECTED | tracked_obj | progress 0-100% |
| COUNTDOWN | time | "3...2...1..." |
| PICKING | grasp | robot commands |

---

## 📐 Coordinate Transform

```
PIXEL (u, v)                    ROBOT (x, y)
┌─────────────┐                 ┌─────────────┐
│ Camera      │  Homography     │ Robot       │
│ 640×480     │ ───────────────▶│ Workspace   │
│ pixels      │    H (3×3)      │ mm          │
└─────────────┘                 └─────────────┘

robot_xy = H × [u, v, 1]ᵀ  (normalized)
```

### Angle Transform
```python
robot_r = ROBOT_R_OFFSET - camera_angle
#       = -25.55° - camera_angle
```

---

## 📏 Height Calculation

```
Z_MEASURE (120mm) ─────────── Robot position
        │
        │  ↕ lidar_dist
        │
        ▼
   Object Top ─────────────── Calculated
        │
        │  ↕ object height
        │
Z_FLOOR (-64mm) ─────────── Ground

z_grasp = Z_MEASURE - lidar_dist + OFFSET + CORRECTION
```

---

## 🦾 Gripper Control

```
Width (mm) ──▶ Interpolation ──▶ Angle (°) ──▶ Serial "G{angle}"
   25mm    ──▶  [calibration]  ──▶   67°   ──▶    "G67\n"
```

| Width | Angle |
|-------|-------|
| 54mm | 22° |
| 40mm | 50° |
| 23mm | 70° |
| 0mm | 96° |

---

## 📡 Communication

### Dobot (TCP/IP)
```
PC ──────▶ "MovJ(x,y,z,r)\n" ──────▶ Robot
PC ◀────── "0,{},MovJ();"   ◀────── Robot
```

### ESP32 (Serial)
```
PC ──────▶ "G45\n"          ──────▶ ESP32 (Gripper)
PC ──────▶ "L\n"            ──────▶ ESP32 (LIDAR)
PC ◀────── "LIDAR:185\n"    ◀────── ESP32
```
