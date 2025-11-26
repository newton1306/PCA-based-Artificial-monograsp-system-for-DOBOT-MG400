"""
Camera-to-Robot Homography Calculator
ใช้สำหรับคำนวณ Homography Matrix จาก 4 จุด calibration

Workflow:
1. รัน: python capture_pixel_coords.py (คลิกหา 4 จุด)
2. รัน: python calibration_calculator.py (คำนวณ homography)
3. Copy ผลลัพธ์ไปใส่ใน robot_deployment.ipynb
"""

import cv2
import numpy as np
import os

# =============================================================================
# ขั้นตอนที่ 1: โหลด PIXEL COORDINATES (จาก capture_pixel_coords.py)
# =============================================================================
PIXEL_FILE = 'calibration_pixels.npy'

if not os.path.exists(PIXEL_FILE):
    print("="*60)
    print("❌ ERROR: ไม่พบไฟล์ pixel coordinates")
    print("="*60)
    print(f"\nไฟล์ '{PIXEL_FILE}' ไม่พบ!")
    print("\nกรุณารันโปรแกรมนี้ก่อน:")
    print("  python capture_pixel_coords.py")
    print("\nโปรแกรมจะให้คุณ:")
    print("  1. ถ่ายภาพด้วย camera")
    print("  2. คลิกหา pixel coordinates ของ marker 4 จุด")
    print("  3. บันทึกลงไฟล์ calibration_pixels.npy")
    print("\nจากนั้นค่อยรัน calibration_calculator.py นี้อีกครั้ง")
    print("="*60)
    exit(1)

# โหลด pixel coordinates
pixel_points = np.load(PIXEL_FILE)
print("="*60)
print("Camera-to-Robot Calibration")
print("="*60)
print(f"\n✅ Loaded pixel coordinates from: {PIXEL_FILE}")

# =============================================================================
# ขั้นตอนที่ 2: ROBOT COORDINATES (จาก DOBOT STUDIO - ค่าคงที่)
# =============================================================================
# ⚠️ ค่าเหล่านี้วัดจาก DOBOT STUDIO แล้ว ไม่ต้องเปลี่ยน!

robot_points = np.array([
    [96, 119],   # A (Top-Left) - X, Y in mm
    [-7, 119],   # B (Top-Right)
    [95, -13],   # C (Bottom-Left)
    [-8, -13]    # D (Bottom-Right)
], dtype=np.float32)

# =============================================================================
# แสดงข้อมูล
# =============================================================================
print("\n📍 Pixel Coordinates (from Camera):")
for i, label in enumerate(['A', 'B', 'C', 'D']):
    print(f"  {label}: ({pixel_points[i][0]:.0f}, {pixel_points[i][1]:.0f})")

print("\n🤖 Robot Coordinates (from DOBOT STUDIO - Fixed):")
for i, label in enumerate(['A', 'B', 'C', 'D']):
    print(f"  {label}: ({robot_points[i][0]:.1f}, {robot_points[i][1]:.1f}) mm")

# =============================================================================
# คำนวณ Homography Matrix
# =============================================================================
try:
    H, status = cv2.findHomography(pixel_points, robot_points)
    
    print("\n" + "="*60)
    print("✅ HOMOGRAPHY MATRIX")
    print("="*60)
    print(H)
    
    # บันทึกลงไฟล์
    np.save('homography_matrix.npy', H)
    print("\n✅ Saved to: homography_matrix.npy")
    
    print("\n" + "="*60)
    print("📋 Copy ค่านี้ไปใส่ใน robot_deployment.ipynb:")
    print("="*60)
    print("# Section 2️⃣: Configure Robot Connection")
    print("# แทนที่ HOMOGRAPHY_MATRIX เดิม\n")
    print(f"HOMOGRAPHY_MATRIX = np.array({H.tolist()}, dtype=np.float32)")
    
    # ทดสอบความถูกต้อง
    print("\n" + "="*60)
    print("🧪 Verification (ควร error < 5mm):")
    print("="*60)
    
    max_error_x = 0
    max_error_y = 0
    
    for i, label in enumerate(['A', 'B', 'C', 'D']):
        # Transform pixel → robot
        px, py = pixel_points[i]
        pixel_pt = np.array([[px, py]], dtype=np.float32).reshape(-1, 1, 2)
        robot_pt = cv2.perspectiveTransform(pixel_pt, H)
        calc_x, calc_y = robot_pt[0][0]
        
        # Compare with actual
        actual_x, actual_y = robot_points[i]
        error_x = abs(calc_x - actual_x)
        error_y = abs(calc_y - actual_y)
        
        max_error_x = max(max_error_x, error_x)
        max_error_y = max(max_error_y, error_y)
        
        status_icon = "✅" if (error_x < 5 and error_y < 5) else "⚠️"
        print(f"  {status_icon} {label}: Error X={error_x:.2f}mm, Y={error_y:.2f}mm")
    
    print(f"\nMax error: X={max_error_x:.2f}mm, Y={max_error_y:.2f}mm")
    
    if max_error_x < 5 and max_error_y < 5:
        print("✅ Calibration quality: EXCELLENT")
    elif max_error_x < 10 and max_error_y < 10:
        print("⚠️ Calibration quality: ACCEPTABLE (but could be better)")
    else:
        print("❌ Calibration quality: POOR - Consider recalibrating")
        print("   Possible issues:")
        print("   - Wrong order of points (pixel vs robot mismatch)")
        print("   - Camera moved during calibration")
        print("   - Markers not clearly visible")
    
    print("\n" + "="*60)
    print("🎯 Next Steps:")
    print("="*60)
    print("1. ✅ Homography Matrix calculated")
    print("2. ✅ Saved to homography_matrix.npy")
    print("3. ⏳ Copy the HOMOGRAPHY_MATRIX code above")
    print("4. ⏳ Paste into robot_deployment.ipynb")
    print("     → Section 2️⃣: Configure Robot Connection")
    print("     → Replace the existing HOMOGRAPHY_MATRIX")
    print("5. ⏳ Test with robot!")
    print("="*60)
    
except Exception as e:
    print("\n" + "="*60)
    print("❌ ERROR during calculation")
    print("="*60)
    print(f"Error: {e}")
    print("\n⚠️ กรุณาตรวจสอบ:")
    print("  1. pixel_points มาจาก camera (รัน capture_pixel_coords.py)")
    print("  2. robot_points ถูกต้อง (ค่าจาก DOBOT STUDIO)")
    print("  3. ลำดับของจุดตรงกัน (A กับ A, B กับ B, ...)")
    print("  4. มีจุดครบ 4 จุด")
    print("="*60)

