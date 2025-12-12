"""
🎯 Simple Calibration Tool
ไฟล์เดียวครบจบ: จับ pixel + ใส่ robot coords + คำนวณ Homography

วิธีใช้:
1. python calibrate.py
2. กด SPACE เพื่อถ่ายภาพ
3. คลิกที่มุม A, B, C, D ตามลำดับ
4. ใส่ค่า Robot coordinates (X, Y) ของแต่ละมุม
5. ได้ Homography Matrix ไป copy ใส่ notebook
"""

import cv2
import numpy as np

# =============================================================================
# Configuration
# =============================================================================
CAMERA_ID = 2

# =============================================================================
# Step 1: Capture Image
# =============================================================================
print("="*60)
print("🎯 Simple Calibration Tool")
print("="*60)
print(f"\nCamera ID: {CAMERA_ID}")
print("กด SPACE เพื่อถ่ายภาพ | กด Q เพื่อยกเลิก\n")

cap = cv2.VideoCapture(CAMERA_ID)
if not cap.isOpened():
    print(f"❌ ไม่สามารถเปิดกล้อง {CAMERA_ID}")
    exit(1)

frame = None
while True:
    ret, current_frame = cap.read()
    if not ret:
        break
    
    display = current_frame.copy()
    cv2.putText(display, "SPACE = Capture | Q = Quit", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow('Camera', display)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord(' '):
        frame = current_frame.copy()
        print("✓ ถ่ายภาพแล้ว!")
        break
    elif key == ord('q'):
        print("ยกเลิก")
        cap.release()
        cv2.destroyAllWindows()
        exit(0)

cap.release()
cv2.destroyAllWindows()

# Save image
cv2.imwrite('calibration_image.jpg', frame)
print("✓ บันทึกภาพ: calibration_image.jpg")

# =============================================================================
# Step 2: Click on 4 Corners (A, B, C, D)
# =============================================================================
print("\n" + "="*60)
print("🖱️ คลิกที่มุม A → B → C → D ตามลำดับ")
print("="*60)
print("  A = มุมบนซ้าย")
print("  B = มุมบนขวา")
print("  C = มุมล่างซ้าย")
print("  D = มุมล่างขวา")
print("\nปิดหน้าต่างเมื่อคลิกครบ 4 จุด\n")

pixel_coords = []
labels = ['A', 'B', 'C', 'D']
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]  # Red, Green, Blue, Yellow

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(pixel_coords) < 4:
        pixel_coords.append([x, y])
        idx = len(pixel_coords) - 1
        label = labels[idx]
        color = colors[idx]
        
        # Draw on image
        cv2.circle(param, (x, y), 8, color, -1)
        cv2.circle(param, (x, y), 12, color, 2)
        cv2.putText(param, f"{label}:({x},{y})", (x+15, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.imshow('Click A, B, C, D', param)
        
        print(f"✓ {label}: ({x}, {y})")
        
        if len(pixel_coords) == 4:
            print("\n✅ ครบ 4 จุดแล้ว! ปิดหน้าต่างได้")

click_image = frame.copy()
cv2.namedWindow('Click A, B, C, D')
cv2.setMouseCallback('Click A, B, C, D', mouse_callback, click_image)
cv2.imshow('Click A, B, C, D', click_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

if len(pixel_coords) != 4:
    print(f"❌ ต้องคลิก 4 จุด (ได้แค่ {len(pixel_coords)} จุด)")
    exit(1)

# Save clicked image
cv2.imwrite('calibration_marked.jpg', click_image)

# =============================================================================
# Step 3: Input Robot Coordinates
# =============================================================================
print("\n" + "="*60)
print("🤖 ใส่ค่า Robot Coordinates (X, Y) ของแต่ละมุม")
print("="*60)
print("(ค่าที่อ่านจาก Dobot Studio Online mode)")
print()

robot_coords = []
for i, label in enumerate(labels):
    px, py = pixel_coords[i]
    print(f"มุม {label} (Pixel: {px}, {py})")
    
    while True:
        try:
            x = float(input(f"  Robot X: "))
            y = float(input(f"  Robot Y: "))
            robot_coords.append([x, y])
            print()
            break
        except ValueError:
            print("  ❌ ใส่ตัวเลขเท่านั้น!")

# =============================================================================
# Step 4: Calculate Homography Matrix
# =============================================================================
print("="*60)
print("📐 คำนวณ Homography Matrix...")
print("="*60)

pixel_points = np.array(pixel_coords, dtype=np.float32)
robot_points = np.array(robot_coords, dtype=np.float32)

H, status = cv2.findHomography(pixel_points, robot_points)

print("\n✅ Homography Matrix:\n")
print("HOMOGRAPHY_MATRIX = np.array([")
for row in H:
    print(f"    [{row[0]}, {row[1]}, {row[2]}],")
print("], dtype=np.float32)")

# =============================================================================
# Step 5: Verify
# =============================================================================
print("\n" + "="*60)
print("🔍 ตรวจสอบความแม่นยำ")
print("="*60)

total_error = 0
for i, label in enumerate(labels):
    px, py = pixel_coords[i]
    rx_actual, ry_actual = robot_coords[i]
    
    # Transform
    point = np.array([px, py, 1], dtype=np.float32)
    result = np.dot(H, point)
    rx_calc = result[0] / result[2]
    ry_calc = result[1] / result[2]
    
    error = np.sqrt((rx_actual - rx_calc)**2 + (ry_actual - ry_calc)**2)
    total_error += error
    
    print(f"{label}: Pixel({px},{py}) → Robot({rx_calc:.1f},{ry_calc:.1f}) vs Actual({rx_actual},{ry_actual}) | Error: {error:.2f}mm")

avg_error = total_error / 4
print(f"\n📊 Average Error: {avg_error:.2f} mm")

if avg_error < 5:
    print("✅ Calibration ดีมาก!")
elif avg_error < 10:
    print("⚠️ Calibration พอใช้ได้")
else:
    print("❌ Calibration ไม่ดี - ลอง calibrate ใหม่")

# =============================================================================
# Save
# =============================================================================
np.save('homography_matrix.npy', H)
print(f"\n✓ บันทึก: homography_matrix.npy")

print("\n" + "="*60)
print("📋 COPY โค้ดนี้ไปใส่ใน robot_deployment.ipynb:")
print("="*60)
print()
print("HOMOGRAPHY_MATRIX = np.array([")
for row in H:
    print(f"    [{row[0]}, {row[1]}, {row[2]}],")
print("], dtype=np.float32)")
print()
print("="*60)
