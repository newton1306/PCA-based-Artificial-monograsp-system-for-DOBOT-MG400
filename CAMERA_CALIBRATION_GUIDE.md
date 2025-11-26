# 📸 Camera Calibration Guide

**คู่มือการทำ Camera Calibration สำหรับ Dobot MG400**

---

## 📋 สารบัญ

1. [ทำไมต้อง Calibrate?](#ทำไมต้อง-calibrate)
2. [อุปกรณ์ที่ต้องเตรียม](#อุปกรณ์ที่ต้องเตรียม)
3. [วิธีที่ 1: 4-Point Method (แนะนำ)](#วิธีที่-1-4-point-method-แนะนำ)
4. [วิธีที่ 2: Checkerboard Method (ละเอียดกว่า)](#วิธีที่-2-checkerboard-method-ละเอียดกว่า)
5. [นำค่าไปใช้ในโค้ด](#นำค่าไปใช้ในโค้ด)
6. [ทดสอบความถูกต้อง](#ทดสอบความถูกต้อง)
7. [Troubleshooting](#troubleshooting)

---

## ทำไมต้อง Calibrate?

### ปัญหา:
- Camera เห็นโลกเป็น **pixel** (เช่น x=320, y=240)
- Robot ทำงานด้วย **millimeters** (เช่น X=300mm, Y=150mm)
- ต้องแปลง **pixel coordinates → robot coordinates**

### ถ้าไม่ Calibrate:
```
❌ Camera เห็นวัตถุที่ pixel (320, 240)
❌ Robot จะไปที่ (320mm, 240mm)??? ← ผิดพลาด!
✅ ต้องแปลงเป็น (280mm, 120mm) ← ตำแหน่งที่ถูกต้อง
```

### Homography Matrix คืออะไร?
เป็น matrix 3x3 ที่ใช้แปลง pixel → robot coordinates:

```python
[robot_x]   [h11  h12  h13]   [pixel_x]
[robot_y] = [h21  h22  h23] × [pixel_y]
[   1   ]   [h31  h32  h33]   [   1   ]
```

---

## อุปกรณ์ที่ต้องเตรียม

### Hardware:
- ✅ Camera ติดตั้งอยู่เหนือ workspace แล้ว (ไม่เคลื่อนที่)
- ✅ Dobot MG400 เปิดและเชื่อมต่อแล้ว
- ✅ Marker 4 ตัว (จุดเล็กๆ ที่เห็นชัดเจน)
  - เหรียญ, สติ๊กเกอร์กลม, หรือวาดจุดบนกระดาษ
  - ขนาดเล็กพอให้จิ้มด้วย robot ได้แม่นยำ

### Software:
- ✅ Dobot Studio (สำหรับควบคุม robot manual)
- ✅ Jupyter Notebook
- ✅ Python libraries: cv2, numpy, matplotlib

---

## วิธีที่ 1: 4-Point Method (แนะนำ)

**เหมาะสำหรับ:** ผู้ที่ต้องการวิธีง่ายและเร็ว

### ขั้นตอนที่ 1: เตรียม Workspace

1. **วาง marker 4 จุด** บน workspace ในรูปแบบสี่เหลี่ยม:

```
    A ●────────────● B
      │            │
      │            │
      │  Workspace │
      │            │
      │            │
    C ●────────────● D
```

**คำแนะนำ:**
- ระยะห่างระหว่างจุด: อย่างน้อย 15-20 cm
- ให้ 4 จุดครอบคลุมพื้นที่ทำงานของ robot
- อยู่ในมุมมองของ camera ทั้งหมด

---

### ขั้นตอนที่ 2: บันทึก Pixel Coordinates

ใช้ Python notebook สำหรับหา pixel coordinates ของ marker แต่ละจุด:

```python
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Capture image
cap = cv2.VideoCapture(1)  # แก้เป็น camera ID ของคุณ
ret, frame = cap.read()
cap.release()

if not ret:
    print("Error: Cannot capture frame")
else:
    # แสดงภาพ
    plt.figure(figsize=(10, 8))
    plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    plt.title("Click on 4 markers: A (Top-Left) → B (Top-Right) → C (Bottom-Left) → D (Bottom-Right)")
    plt.axis('off')
    
    # เก็บค่า coordinates
    coords = []
    
    def onclick(event):
        if event.xdata is not None and event.ydata is not None:
            x, y = int(event.xdata), int(event.ydata)
            coords.append([x, y])
            plt.plot(x, y, 'ro', markersize=10)
            plt.text(x+10, y-10, f'({x},{y})', color='red', fontsize=12)
            plt.draw()
            print(f"Point {len(coords)}: ({x}, {y})")
    
    cid = plt.gcf().canvas.mpl_connect('button_press_event', onclick)
    plt.show()
    
    # บันทึกค่า
    if len(coords) == 4:
        pixel_points = np.array(coords, dtype=np.float32)
        print("\n✓ Pixel coordinates saved:")
        print(pixel_points)
        
        # บันทึกลงไฟล์
        np.save('calibration_pixels.npy', pixel_points)
    else:
        print(f"Error: Need 4 points, got {len(coords)}")
```

**ผลลัพธ์ตัวอย่าง:**
```
Point 1: (145, 98)   ← Marker A (Top-Left)
Point 2: (512, 95)   ← Marker B (Top-Right)
Point 3: (138, 387)  ← Marker C (Bottom-Left)
Point 4: (518, 390)  ← Marker D (Bottom-Right)
```

---

### ขั้นตอนที่ 3: บันทึก Robot Coordinates

ใช้ **Dobot Studio** เคลื่อน robot ไปแตะที่ marker แต่ละจุด:

1. **เปิด Dobot Studio**
2. **Home robot** ก่อน
3. **เคลื่อน robot ไปแตะที่ marker A** (Top-Left)
   - บันทึก **X, Y** (ไม่ต้องสนใจ Z)
   - เช่น: X=220, Y=180
4. **ทำซ้ำสำหรับ B, C, D**

**บันทึกค่าใน Python:**

```python
# Robot coordinates (mm) ตามลำดับ A, B, C, D
robot_points = np.array([
    [220, 180],   # A: Top-Left (X, Y)
    [420, 185],   # B: Top-Right
    [215, -120],  # C: Bottom-Left
    [425, -115],  # D: Bottom-Right
], dtype=np.float32)

print("Robot coordinates:")
print(robot_points)

# บันทึกลงไฟล์
np.save('calibration_robot.npy', robot_points)
```

**💡 Tips:**
- ใช้ jog mode ใน Dobot Studio เคลื่อนช้าๆ
- ตรวจสอบว่า gripper/ปลาย end-effector แตะจุดพอดี
- บันทึกค่าจาก panel ของ Dobot Studio

---

### ขั้นตอนที่ 4: คำนวณ Homography Matrix

```python
import cv2
import numpy as np

# โหลดค่าที่บันทึกไว้
pixel_points = np.load('calibration_pixels.npy')
robot_points = np.load('calibration_robot.npy')

print("Pixel points:")
print(pixel_points)
print("\nRobot points:")
print(robot_points)

# คำนวณ Homography Matrix
H, status = cv2.findHomography(pixel_points, robot_points)

print("\n" + "="*60)
print("✓ HOMOGRAPHY MATRIX (นำไปใช้ในโค้ด)")
print("="*60)
print(H)

# บันทึกไฟล์
np.save('homography_matrix.npy', H)

# พิมพ์ในรูปแบบที่คัดลอกง่าย
print("\n" + "="*60)
print("📋 Copy ค่านี้ไปใส่ใน notebook:")
print("="*60)
print(f"HOMOGRAPHY_MATRIX = np.array({H.tolist()}, dtype=np.float32)")
```

**ผลลัพธ์ตัวอย่าง:**
```python
HOMOGRAPHY_MATRIX = np.array([
    [0.5423, 0.0156, 141.23],
    [0.0089, 0.6234, -45.67],
    [0.00001, 0.00002, 1.0]
], dtype=np.float32)
```

---

### ขั้นตอนที่ 5: ทดสอบการแปลง

```python
import cv2
import numpy as np

# โหลด Homography Matrix
H = np.load('homography_matrix.npy')

def pixel_to_robot(pixel_x, pixel_y, H):
    """แปลง pixel → robot coordinates"""
    pixel_point = np.array([[pixel_x, pixel_y]], dtype=np.float32)
    pixel_point = pixel_point.reshape(-1, 1, 2)
    robot_point = cv2.perspectiveTransform(pixel_point, H)
    robot_x = robot_point[0][0][0]
    robot_y = robot_point[0][0][1]
    return robot_x, robot_y

# ทดสอบกับจุดตรงกลางภาพ
test_pixel_x = 320
test_pixel_y = 240

robot_x, robot_y = pixel_to_robot(test_pixel_x, test_pixel_y, H)

print(f"Pixel ({test_pixel_x}, {test_pixel_y}) → Robot ({robot_x:.1f}, {robot_y:.1f}) mm")

# ทดสอบกับ marker points ที่รู้ค่า
print("\nVerification:")
for i, (px, py) in enumerate(pixel_points):
    rx, ry = pixel_to_robot(px, py, H)
    expected_x, expected_y = robot_points[i]
    error_x = abs(rx - expected_x)
    error_y = abs(ry - expected_y)
    print(f"Point {i+1}: Error X={error_x:.1f}mm, Y={error_y:.1f}mm")
    
print("\n✓ Error ควรน้อยกว่า 5mm")
```

---

## วิธีที่ 2: Checkerboard Method (ละเอียดกว่า)

**เหมาะสำหรับ:** ผู้ที่ต้องการความแม่นยำสูง

### ขั้นตอนที่ 1: พิมพ์ Checkerboard Pattern

1. ดาวน์โหลด checkerboard pattern:
   - ขนาด: 7×7 หรือ 9×6 squares
   - ขนาดแต่ละช่อง: 25mm × 25mm
   - หรือสร้างเองใน Word/PowerPoint

2. **พิมพ์และวางบน workspace**
   - ติดกับพื้นผิวให้แน่น (ไม่โค้งงอ)
   - อยู่ในมุมมองของ camera

### ขั้นตอนที่ 2: Capture หลายภาพ

```python
import cv2
import numpy as np

# Pattern size (จำนวนมุมภายใน)
pattern_size = (6, 8)  # 7×9 squares = 6×8 corners
square_size = 25  # mm

# Capture multiple images
cap = cv2.VideoCapture(1)
images = []

print("Press SPACE to capture, Q to finish")
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    cv2.imshow('Calibration', frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord(' '):  # SPACE
        images.append(frame.copy())
        print(f"Captured {len(images)} images")
    elif key == ord('q'):  # Q
        break

cap.release()
cv2.destroyAllWindows()
print(f"\n✓ Captured {len(images)} images")
```

### ขั้นตอนที่ 3: Camera Calibration

```python
import cv2
import numpy as np

# Prepare object points
objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
objp *= square_size

objpoints = []  # 3D points in real world
imgpoints = []  # 2D points in image

# Find corners in each image
for img in images:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
    
    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)

# Calibrate
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)

print("Camera Matrix:")
print(camera_matrix)
print("\nDistortion Coefficients:")
print(dist_coeffs)

# Save
np.save('camera_matrix.npy', camera_matrix)
np.save('dist_coeffs.npy', dist_coeffs)
```

**หมายเหตุ:** วิธีนี้ซับซ้อนกว่า แนะนำใช้ 4-Point Method ก่อน

---

## นำค่าไปใช้ในโค้ด

### 📍 ตำแหน่งที่ต้องแก้: `robot_deployment.ipynb`

เปิดไฟล์ [`robot_deployment.ipynb`](file:///c:/Users/CPE%20KMUTT/Music/Artificial_MonoGrasp/notebook_v3/robot_deployment.ipynb)

ไปที่ **Cell: "Configure Robot Connection"** (Section 2️⃣)

**แก้จาก:**
```python
# 2. Homography Matrix (จาก camera calibration)
# ⚠️ ต้องทำ calibration ก่อน!
HOMOGRAPHY_MATRIX = np.array([
    [1.2,  0.01, -150],   # ← ค่าปลอม! ต้องเปลี่ยน
    [0.02, 1.3,   200],
    [0.0001, 0.0002, 1]
], dtype=np.float32)
```

**เป็น:** (ใส่ค่าที่คำนวณได้จริง)
```python
# 2. Homography Matrix (จาก camera calibration)
HOMOGRAPHY_MATRIX = np.array([
    [0.5423, 0.0156, 141.23],   # ← ค่าจากการ calibrate จริง
    [0.0089, 0.6234, -45.67],
    [0.00001, 0.00002, 1.0]
], dtype=np.float32)
```

**หรือโหลดจากไฟล์:**
```python
# 2. Homography Matrix (โหลดจากไฟล์)
HOMOGRAPHY_MATRIX = np.load('homography_matrix.npy')
print("✓ Loaded Homography Matrix:")
print(HOMOGRAPHY_MATRIX)
```

---

## ทดสอบความถูกต้อง

### วิธีที่ 1: ทดสอบกับจุดที่รู้ค่า

1. **วางวัตถุที่ตำแหน่งที่รู้** (เช่น X=300mm, Y=100mm)
2. **ใช้ vision system detect**
3. **ดูว่าแปลงเป็น robot coordinates ได้ถูกหรือไม่**

```python
# ใน notebook cell ใหม่
# สมมติ detect ได้ pixel (350, 220)
test_pixel_x = 350
test_pixel_y = 220

# แปลงด้วย homography
H = HOMOGRAPHY_MATRIX
pixel_point = np.array([[test_pixel_x, test_pixel_y]], dtype=np.float32).reshape(-1, 1, 2)
robot_point = cv2.perspectiveTransform(pixel_point, H)
robot_x = robot_point[0][0][0]
robot_y = robot_point[0][0][1]

print(f"Pixel: ({test_pixel_x}, {test_pixel_y})")
print(f"Robot: ({robot_x:.1f}, {robot_y:.1f}) mm")
print(f"Expected: (300.0, 100.0) mm")
print(f"Error: X={abs(robot_x-300):.1f}mm, Y={abs(robot_y-100):.1f}mm")

# Error ควร < 10mm
```

### วิธีที่ 2: ทดสอบด้วย Robot จริง

```python
# ใน robot_deployment.ipynb
# หลังจาก connect robot แล้ว

# 1. วางวัตถุที่เห็นได้ชัด
# 2. Detect และหา best grasp
result = pipeline.process_frame(frame, detect_objects=True)
best_grasp = pipeline.get_best_grasp(result)

# 3. แปลงเป็น robot coordinates
cy, cx = best_grasp.center
robot_x, robot_y = robot.pixel_to_robot(cx, cy)

print(f"Vision detected at pixel ({cx:.0f}, {cy:.0f})")
print(f"Will move robot to ({robot_x:.1f}, {robot_y:.1f}) mm")

# 4. เคลื่อนช้าๆ ไปดู (ไม่จับ แค่ชี้)
confirm = input("Move robot to check position? (y/n): ")
if confirm == 'y':
    robot.move_to(robot_x, robot_y, 150, 0)  # ความสูง 150mm (ปลอดภัย)
    print("Check if robot is pointing at the object!")
```

**ผลลัพธ์ที่คาดหวัง:**
- ✅ Robot ชี้ไปที่ตำแหน่งใกล้กับวัตถุ (error < 10mm)
- ❌ Robot ชี้ผิดที่มาก → ต้องทำ calibration ใหม่

---

## Troubleshooting

### ปัญหา: Error สูงมาก (> 20mm)

**สาเหตุ:**
1. ❌ Marker 4 จุดไม่ได้วางเป็นรูปสี่เหลี่ยมที่ดี
2. ❌ Camera เคลื่อนที่ระหว่าง calibration
3. ❌ บันทึก robot coordinates ผิด

**วิธีแก้:**
- วาง marker ให้เป็นสี่เหลี่ยมมากขึ้น
- ตรึง camera ให้แน่น
- ทำ calibration ใหม่ทั้งหมด

---

### ปัญหา: Error ไม่สม่ำเสมอ (บางจุดถูก บางจุดผิด)

**สาเหตุ:**
- Lens distortion ของ camera

**วิธีแก้:**
- ใช้ Checkerboard Method แทน
- หรือจำกัด workspace ให้เล็กลง (ไม่ใช้ขอบๆ)

---

### ปัญหา: Camera เคลื่อนที่หลัง calibrate

**วิธีแก้:**
- ⚠️ **ต้องทำ calibration ใหม่ทันที!**
- ตรึง camera ให้แน่นกว่าเดิม

---

## 📝 Checklist

ก่อนใช้งานจริง ตรวจสอบว่า:

- [ ] วาง marker 4 จุดครอบคลุม workspace
- [ ] Capture ภาพและบันทึก pixel coordinates
- [ ] ใช้ robot บันทึก robot coordinates ของแต่ละจุด
- [ ] คำนวณ Homography Matrix ด้วย `cv2.findHomography()`
- [ ] บันทึก matrix ลงไฟล์ `homography_matrix.npy`
- [ ] นำค่าไปใส่ใน `robot_deployment.ipynb` → Cell "Configure Robot Connection"
- [ ] ทดสอบความถูกต้อง (error < 10mm)
- [ ] ไม่เคลื่อนย้าย camera หลัง calibration!

---

## 🎯 สรุป

### 4-Point Method (แนะนำ):
```
1. วาง marker 4 จุด
2. บันทึก pixel coords (ใช้ matplotlib click)
3. บันทึก robot coords (ใช้ Dobot Studio)
4. คำนวณ H = cv2.findHomography()
5. ใส่ใน notebook → HOMOGRAPHY_MATRIX
```

### ตำแหน่งที่ใช้:
- 📍 **หลัก:** `robot_deployment.ipynb` → Section 2️⃣ → `HOMOGRAPHY_MATRIX`
- 📍 **ภายใน:** `robot_control.py` → `pixel_to_robot()` function (ถูกเรียกอัตโนมัติ)

### Accuracy Goal:
- ✅ Error < 5mm = ดีมาก
- ⚠️ Error 5-10mm = ใช้งานได้
- ❌ Error > 10mm = ต้อง calibrate ใหม่

---

**Good luck! 🚀**

หากมีปัญหาหรือต้องการความช่วยเหลือเพิ่มเติม สามารถดูได้จาก:
- [ROBOT_DEPLOYMENT_GUIDE.md](file:///c:/Users/CPE%20KMUTT/Music/Artificial_MonoGrasp/notebook_v3/ROBOT_DEPLOYMENT_GUIDE.md) (คู่มือทั่วไป)
- [robot_deployment.ipynb](file:///c:/Users/CPE%20KMUTT/Music/Artificial_MonoGrasp/notebook_v3/robot_deployment.ipynb) (Notebook สำหรับรัน robot)
