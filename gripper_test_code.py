# =====================================================
# 🧪 Gripper Test Cell - Copy to Notebook after Cell 6
# =====================================================
# วางไว้หลังจาก Connect Devices (Cell 6)
# =====================================================

"""
# =================================================================
# 🧪 Test Gripper Dynamic Control
# =================================================================
# ทดสอบการกางหุบตามความกว้างที่ระบุ (มม.)

print("=" * 50)
print("🧪 Gripper Dynamic Test")
print("=" * 50)
print("Commands:")
print("  [number] = Set gripper width (mm), e.g. '30' = 30mm")
print("  o = Open fully (74mm)")  
print("  c = Close fully (5mm)")
print("  t = Test sequence (open 50mm → grip 30mm → release)")
print("  q = Quit")
print("=" * 50)

while True:
    cmd = input("\n🦾 Enter command: ").strip().lower()
    
    if cmd == 'q':
        print("Exit test mode")
        break
    
    elif cmd == 'o':
        # Open fully
        angle = gripper.mm_to_angle(GRIPPER_MAX_WIDTH_MM)
        print(f"Opening to {GRIPPER_MAX_WIDTH_MM}mm ({angle}°)")
        gripper.send_command(f'G{angle}')
        
    elif cmd == 'c':
        # Close fully
        angle = gripper.mm_to_angle(GRIPPER_MIN_WIDTH_MM)
        print(f"Closing to {GRIPPER_MIN_WIDTH_MM}mm ({angle}°)")
        gripper.send_command(f'G{angle}')
        
    elif cmd == 't':
        # Test sequence
        print("\n--- Test Sequence ---")
        
        print("\n[1/4] Opening for 40mm object...")
        gripper.open_for_object(40)
        time.sleep(2)
        
        print("\n[2/4] Gripping 40mm object...")
        gripper.grip_object(40)
        time.sleep(2)
        
        print("\n[3/4] Releasing...")
        gripper.release()
        time.sleep(2)
        
        print("\n[4/4] Return to default open...")
        gripper.open_for_object(50)
        
        print("\n✅ Test sequence complete!")
        
    else:
        # Try parse as width in mm
        try:
            width_mm = float(cmd)
            if GRIPPER_MIN_WIDTH_MM <= width_mm <= GRIPPER_MAX_WIDTH_MM:
                angle = gripper.mm_to_angle(width_mm)
                print(f"Setting width to {width_mm}mm ({angle}°)")
                gripper.send_command(f'G{angle}')
            else:
                print(f"⚠️ Width must be {GRIPPER_MIN_WIDTH_MM}-{GRIPPER_MAX_WIDTH_MM}mm")
        except ValueError:
            print("❓ Unknown command. Use number (mm), o, c, t, or q")
"""

# =====================================================
# 🧪 Alternative: Visual Test with Camera
# =====================================================
"""
# =================================================================
# 🧪 Visual Gripper Test (with Camera Preview)
# =================================================================
# ดูขนาดวัตถุจากกล้อง แล้วทดสอบกางหุบ

print("=" * 50)
print("🧪 Visual Gripper Test")
print("=" * 50)
print("Controls:")
print("  Click object = Show grip width")
print("  SPACE = Test grip for clicked object")
print("  O = Open for object")
print("  G = Grip object")
print("  R = Release")
print("  Q = Quit")
print("=" * 50)

test_object = None

def mouse_test_callback(event, x, y, flags, param):
    global test_object
    if event == cv2.EVENT_LBUTTONDOWN:
        for obj in detected_objects:
            ox, oy, ow, oh, cx, cy, contour = obj
            if ox <= x <= ox+ow and oy <= y <= oy+oh:
                test_object = obj
                width_mm, height_mm, grip_width_mm = detector.measure_object(obj, PIXELS_PER_MM)
                print(f"\n📦 Object selected:")
                print(f"   Size: {width_mm:.1f} x {height_mm:.1f} mm")
                print(f"   Grip width: {grip_width_mm:.1f} mm")
                print(f"   Press O=Open, G=Grip, R=Release")
                break

cap = cv2.VideoCapture(CAMERA_ID)
if cap.isOpened():
    cv2.namedWindow('Gripper Test')
    cv2.setMouseCallback('Gripper Test', mouse_test_callback)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        detected_objects = detector.detect_objects(frame, THRESHOLD_VALUE, MIN_OBJECT_AREA)
        
        for obj in detected_objects:
            x, y, w, h, cx, cy, contour = obj
            width_mm, height_mm, grip_width_mm = detector.measure_object(obj, PIXELS_PER_MM)
            
            is_selected = test_object is not None and (x, y) == (test_object[0], test_object[1])
            color = (0, 0, 255) if is_selected else (0, 255, 0)
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"Grip: {grip_width_mm:.0f}mm", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        cv2.putText(frame, "Click=Select | O=Open | G=Grip | R=Release | Q=Quit", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        if test_object:
            _, _, grip_width = detector.measure_object(test_object, PIXELS_PER_MM)
            cv2.putText(frame, f"Selected: {grip_width:.1f}mm", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        cv2.imshow('Gripper Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('o') and test_object:
            _, _, grip_width = detector.measure_object(test_object, PIXELS_PER_MM)
            gripper.open_for_object(grip_width)
        elif key == ord('g') and test_object:
            _, _, grip_width = detector.measure_object(test_object, PIXELS_PER_MM)
            gripper.grip_object(grip_width)
        elif key == ord('r'):
            gripper.release()
    
    cap.release()
    cv2.destroyAllWindows()
"""

print("""
=====================================================
📋 วิธีใช้งาน:
=====================================================
Copy code ด้านบนไปใส่ใน notebook หลัง Cell 6 (Connect Devices)

มี 2 แบบให้เลือก:
1. Text Mode - พิมพ์ค่าความกว้าง (mm) ในคอนโซล
2. Visual Mode - คลิกวัตถุจากกล้อง แล้วกด O/G/R

ทั้งสองแบบจะทำงานโดยใช้ค่าจากกล้องควบคุม gripper
=====================================================
""")
