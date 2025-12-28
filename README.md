# 🤖 LIDAR Grasp Detection System v13

**ระบบหยิบจับวัตถุอัตโนมัติด้วย LIDAR + Camera + Dobot MG400**

## ✨ Overview

ระบบ Grasp Detection สำหรับหุ่นยนต์ Dobot MG400 ที่ใช้ **LIDAR** วัดความสูงวัตถุจริง และ **Camera** ตรวจจับตำแหน่ง ทำให้หยิบจับวัตถุได้แม่นยำ

### Key Features

- ✅ **ไม่ใช้ YOLO** - ใช้ Color + Edge Detection (เร็วกว่า)
- ✅ **LIDAR วัดความสูง** - แม่นยำกว่า Depth Camera
- ✅ **Height-based Correction** - ปรับ Z ตามความสูงวัตถุ
- ✅ **PCA Grasp Selection** - หามุมจับที่เหมาะสม
- ✅ **Self-contained** - ทุกอย่างอยู่ใน Notebook เดียว

---

## 🛠️ Hardware Requirements

| อุปกรณ์ | รายละเอียด |
|---------|------------|
| **Robot** | Dobot MG400 (TCP/IP: 192.168.1.6) |
| **Camera** | USB Camera |
| **LIDAR** | TF-Luna via ESP32 (COM9) |
| **Gripper** | Servo Gripper via ESP32 |

---

## 📂 File Structure

```
├── 13_sc_best_lidar_grasp_v13_new.ipynb  # ⭐ Main notebook
├── calibrate_for_v13.ipynb               # Calibration notebook
├── homography_matrix.npy                  # Camera-Robot matrix
├── calibration_values_v13.txt             # Saved calibration
└── esp32_gripper_lidar_v11/               # ESP32 code
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install opencv-python numpy pyserial
```

### 2. Calibration (ครั้งแรก)

```bash
jupyter notebook calibrate_for_v13.ipynb
```

Run ทุก cell เพื่อ calibrate:
1. **PIXELS_PER_MM** - วัดไม้บรรทัด
2. **HOMOGRAPHY_MATRIX** - 4-point calibration
3. **ROBOT_R_OFFSET** - ปรับมุม gripper
4. **Z_FLOOR** - ความสูงพื้น
5. **LIDAR offsets** - X, Y, Physical, Correction
6. **HEIGHT_CORRECTION_FACTOR** - ปรับตามความสูง
7. **Gripper widths** - วัดความกว้าง

### 3. Run Main System

```bash
jupyter notebook 13_sc_best_lidar_grasp_v13_new.ipynb
```

---

## ⚙️ Configuration (v13)

```python
# Camera Calibration
PIXELS_PER_MM = 2.7703

# Robot R Rotation
ROBOT_R_OFFSET = -25.55

# Z Heights
Z_FLOOR = -64
Z_MEASURE = 120

# LIDAR Configuration
LIDAR_PHYSICAL_OFFSET = 60   # mm
LIDAR_CORRECTION = -21       # mm
LIDAR_X_OFFSET = 25.08
LIDAR_Y_OFFSET = 20.71

# Height-based Correction
HEIGHT_CORRECTION_FACTOR = 0.115

# Gripper
GRIPPER_MAX_WIDTH_MM = 54
GRIPPER_OPEN_MARGIN_MM = 5
GRIPPER_GRIP_MARGIN_MM = 5

# Detection (Color + Edge)
MIN_OBJECT_AREA = 800
MAX_OBJECT_AREA = 50000
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| **Click** | เลือกวัตถุ |
| **SPACE** | Execute Pick |
| **H** | Home Robot |
| **R** | Reset Selection |
| **C** | Reconnect All |
| **Q** | Quit |

---

## 📊 How It Works

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Camera    │───>│   Detection  │───>│ PCA Grasp   │
│  (Color+    │    │  (Saturation │    │  Selector   │
│   Edge)     │    │   + Edge)    │    │             │
└─────────────┘    └──────────────┘    └──────┬──────┘
                                              │
┌─────────────┐    ┌──────────────┐    ┌──────▼──────┐
│   Gripper   │<───│    Robot     │<───│   LIDAR     │
│   (Grip)    │    │  (MovJ/Z)    │    │  (Height)   │
└─────────────┘    └──────────────┘    └─────────────┘
```

### LIDAR Z Calculation (v13)

```python
z_base = Z_MEASURE - lidar_reading + LIDAR_PHYSICAL_OFFSET
z_corrected = z_base + LIDAR_CORRECTION
height_correction = estimated_height * HEIGHT_CORRECTION_FACTOR
z_grasp = z_corrected - height_correction
```

---

## 🔧 Troubleshooting

### ❌ ไม่เจอวัตถุ
- ปรับ `MIN_OBJECT_AREA` / `MAX_OBJECT_AREA`
- ตรวจสอบแสง (ควรสม่ำเสมอ)

### ❌ Gripper ลงลึกเกินไป
- เพิ่ม `HEIGHT_CORRECTION_FACTOR`
- ตรวจสอบ `LIDAR_CORRECTION`

### ❌ Gripper ไม่ถึงวัตถุ
- ลด `HEIGHT_CORRECTION_FACTOR`
- ตรวจสอบ `LIDAR_PHYSICAL_OFFSET`

### ❌ พิกัด X,Y ผิด
- Recalibrate `HOMOGRAPHY_MATRIX`
- ตรวจสอบ `LIDAR_X_OFFSET` / `LIDAR_Y_OFFSET`

---

## 📈 Version History

| Version | Changes |
|---------|---------|
| v13 | ✅ Color+Edge Detection (No YOLO), Height-based Correction |
| v12 | LIDAR correction factor |
| v11 | Basic LIDAR integration |
| v10 | Hybrid Depth+LIDAR |

---

## 📝 Credits

- **Robot**: [Dobot MG400](https://www.dobot-robots.com/products/desktop-four-axis/mg400.html)
- **LIDAR**: TF-Luna ToF Sensor
- **Detection**: OpenCV Color + Edge Detection
- **Grasp**: PCA-based Grasp Selection

---

**Version**: 13.0 (LIDAR Grasp - No YOLO)  
**Last Updated**: December 2025
