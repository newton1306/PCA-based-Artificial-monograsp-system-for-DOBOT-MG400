"""
Capture Camera Image and Find Pixel Coordinates
สำหรับหา pixel coordinates ของ marker 4 จุด

วิธีใช้:
1. รันโปรแกรม: python capture_pixel_coords.py
2. กด SPACE เพื่อถ่ายภาพ
3. คลิกที่ marker 4 จุดตามลำดับ: A → B → C → D
4. ปิดหน้าต่างเมื่อเสร็จ
5. ผลลัพธ์จะบันทึกใน calibration_pixels.npy
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Configuration
# =============================================================================
CAMERA_ID = 1  # แก้เป็น camera ID ของคุณ (0, 1, 2, ...)
SAVE_FILE = 'calibration_pixels.npy'

# =============================================================================
# Capture Image
# =============================================================================
print("="*60)
print("📸 Camera Pixel Coordinates Finder")
print("="*60)
print(f"\nUsing Camera ID: {CAMERA_ID}")
print("\n⌨️  Press SPACE to capture image")
print("⌨️  Press Q to quit\n")

cap = cv2.VideoCapture(CAMERA_ID)

if not cap.isOpened():
    print(f"❌ Error: Cannot open camera {CAMERA_ID}")
    print("\nTry different camera IDs:")
    print("  - Change CAMERA_ID in this script")
    print("  - Common values: 0, 1, 2")
    exit(1)

frame = None

while True:
    ret, current_frame = cap.read()
    
    if not ret:
        print("❌ Error: Cannot read from camera")
        break
    
    # แสดง preview
    display = current_frame.copy()
    cv2.putText(display, "Press SPACE to capture", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(display, "Press Q to quit", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imshow('Camera Preview', display)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord(' '):  # SPACE
        frame = current_frame.copy()
        print("✓ Image captured!")
        break
    elif key == ord('q'):  # Q
        print("Cancelled")
        cap.release()
        cv2.destroyAllWindows()
        exit(0)

cap.release()
cv2.destroyAllWindows()

if frame is None:
    print("❌ No image captured")
    exit(1)

# บันทึกภาพ
cv2.imwrite('calibration_image.jpg', frame)
print("✓ Saved image: calibration_image.jpg")

# =============================================================================
# Find Pixel Coordinates
# =============================================================================
print("\n" + "="*60)
print("🖱️  Click on 4 Markers")
print("="*60)
print("\nOrder: A (Top-Left) → B (Top-Right) → C (Bottom-Left) → D (Bottom-Right)")
print("\n⚠️  Click in the SAME ORDER as robot coordinates!")
print("⚠️  Close the matplotlib window when done\n")

coords = []
labels = ['A', 'B', 'C', 'D']

fig, ax = plt.subplots(figsize=(14, 10))
ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
ax.set_title("Click on 4 Markers: A → B → C → D\n(Same order as DOBOT measurements!)", 
             fontsize=14, fontweight='bold')
ax.axis('off')

# วาดคำอธิบาย
instruction_text = (
    "Instructions:\n"
    "1. Click on marker A (Top-Left)\n"
    "2. Click on marker B (Top-Right)\n"
    "3. Click on marker C (Bottom-Left)\n"
    "4. Click on marker D (Bottom-Right)\n"
    "5. Close window when done"
)
ax.text(10, frame.shape[0] - 10, instruction_text,
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
        fontsize=10, verticalalignment='bottom')

def onclick(event):
    if event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)
        
        if len(coords) < 4:
            coords.append([x, y])
            label = labels[len(coords)-1]
            
            # วาดจุด
            ax.plot(x, y, 'ro', markersize=15)
            
            # เขียน label
            ax.text(x+20, y-20, f'{label}: ({x},{y})', 
                   color='red', fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # วงกลม
            circle = plt.Circle((x, y), 10, color='red', fill=False, linewidth=2)
            ax.add_patch(circle)
            
            fig.canvas.draw()
            
            print(f"✓ Point {label}: ({x}, {y})")
            
            if len(coords) == 4:
                print("\n✅ All 4 points captured!")
                print("Close the matplotlib window to continue...")
        else:
            print("⚠️  Already have 4 points. Close the window to continue.")

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()

# =============================================================================
# Save Results
# =============================================================================
if len(coords) != 4:
    print(f"\n❌ Error: Need 4 points, got {len(coords)}")
    print("Please run again and click all 4 markers")
    exit(1)

pixel_points = np.array(coords, dtype=np.float32)

print("\n" + "="*60)
print("✅ PIXEL COORDINATES")
print("="*60)
for i, label in enumerate(labels):
    print(f"  {label}: [{pixel_points[i][0]:.0f}, {pixel_points[i][1]:.0f}]")

# บันทึกลงไฟล์
np.save(SAVE_FILE, pixel_points)
print(f"\n✓ Saved to: {SAVE_FILE}")

print("\n" + "="*60)
print("📋 Copy these values to calibration_calculator.py:")
print("="*60)
print("\npixel_points = np.array([")
for i, label in enumerate(labels):
    x, y = pixel_points[i]
    print(f"    [{x:.0f}, {y:.0f}],    # {label}")
print("], dtype=np.float32)")

print("\n" + "="*60)
print("🎯 Next Steps:")
print("="*60)
print("1. ✅ You have pixel coordinates")
print("2. ✅ You have robot coordinates (from DOBOT STUDIO)")
print("3. ⏳ Update calibration_calculator.py with these pixel values")
print("4. ⏳ Run: python calibration_calculator.py")
print("5. ⏳ Copy Homography Matrix to robot_deployment.ipynb")
print("="*60)
