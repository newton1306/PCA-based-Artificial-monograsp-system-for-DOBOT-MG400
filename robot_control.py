"""
Robot Control for Dobot MG400
สำหรับควบคุมแขนกล Dobot MG400 พร้อมระบบ Grasp Detection
"""

import numpy as np
import cv2
import time
from typing import Tuple, Optional


class DobotController:
    """Controller สำหรับ Dobot MG400"""
    
    def __init__(self, config, homography_matrix: np.ndarray):
        """
        Args:
            config: Configuration object
            homography_matrix: Matrix สำหรับแปลง pixel → robot coordinates
        """
        self.config = config
        self.H = np.array(homography_matrix, dtype=np.float32)
        self.robot = None
        self.is_connected = False
        
        # Robot parameters
        self.safe_height = 100  # mm
        self.grasp_height = 20  # mm
        self.drop_position = (250, 150, 50, 0)  # X, Y, Z, R
        
    def connect(self, port_or_ip: str) -> bool:
        """
        เชื่อมต่อกับ robot
        
        Args:
            port_or_ip: COM port (Windows) หรือ IP address
            
        Returns:
            True ถ้าเชื่อมต่อสำเร็จ
        """
        try:
            from pydobot import Dobot
            
            print(f"กำลังเชื่อมต่อกับ robot ที่ {port_or_ip}...")
            self.robot = Dobot(port=port_or_ip)
            self.is_connected = True
            print("✓ เชื่อมต่อสำเร็จ!")
            
            # Get current position
            pose = self.robot.pose()
            print(f"ตำแหน่งปัจจุบัน: X={pose[0]:.1f}, Y={pose[1]:.1f}, Z={pose[2]:.1f}, R={pose[3]:.1f}")
            
            return True
            
        except ImportError:
            print("✗ ไม่พบ pydobot library")
            print("ติดตั้งด้วย: pip install pydobot")
            return False
            
        except Exception as e:
            print(f"✗ การเชื่อมต่อล้มเหลว: {e}")
            print("\nแนวทางแก้ไข:")
            print("  1. ตรวจสอบสาย USB/Ethernet")
            print("  2. ตรวจสอบ COM port (Windows: Device Manager)")
            print("  3. ตรวจสอบ IP address ถูกต้อง")
            print("  4. ลอง restart robot")
            return False
    
    def home(self) -> bool:
        """Home robot (กลับจุดเริ่มต้น)"""
        if not self.is_connected:
            print("✗ ยังไม่ได้เชื่อมต่อ robot")
            return False
        
        try:
            print("กำลัง Home robot...")
            self.robot.home()
            print("✓ Home สำเร็จ")
            return True
            
        except Exception as e:
            print(f"✗ Home ล้มเหลว: {e}")
            return False
    
    def pixel_to_robot(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        แปลง pixel coordinates → robot coordinates
        
        Args:
            pixel_x, pixel_y: ตำแหน่งใน pixel
            
        Returns:
            (robot_x, robot_y) ในหน่วย mm
        """
        # Create point array for perspective transform
        pixel_point = np.array([[pixel_x, pixel_y]], dtype=np.float32)
        pixel_point = pixel_point.reshape(-1, 1, 2)
        
        # Transform
        robot_point = cv2.perspectiveTransform(pixel_point, self.H)
        
        robot_x = float(robot_point[0][0][0])
        robot_y = float(robot_point[0][0][1])
        
        # Validate workspace limits (ถ้ามีใน config)
        if hasattr(self.config, 'ROBOT_X_MIN'):
            robot_x = np.clip(robot_x, self.config.ROBOT_X_MIN, self.config.ROBOT_X_MAX)
            robot_y = np.clip(robot_y, self.config.ROBOT_Y_MIN, self.config.ROBOT_Y_MAX)
        
        return robot_x, robot_y
    
    def move_to(self, x: float, y: float, z: float, r: float, 
                wait: bool = True, speed: int = 50) -> bool:
        """
        เคลื่อนที่ไปยังตำแหน่งที่กำหนด
        
        Args:
            x, y, z: ตำแหน่งใน mm
            r: มุมหมุนในองศา
            wait: รอให้เคลื่อนที่เสร็จก่อน return
            speed: ความเร็ว (0-100)
        """
        if not self.is_connected:
            print("✗ ยังไม่ได้เชื่อมต่อ robot")
            return False
        
        try:
            self.robot.move_to(x, y, z, r, wait=wait)
            if wait:
                time.sleep(0.5)  # Wait for stability
            return True
            
        except Exception as e:
            print(f"✗ การเคลื่อนที่ล้มเหลว: {e}")
            return False
    
    def control_gripper(self, close: bool) -> bool:
        """
        ควบคุม gripper
        
        Args:
            close: True = ปิด (จับ), False = เปิด (ปล่อย)
        """
        if not self.is_connected:
            return False
        
        try:
            # ปรับตามประเภท gripper ที่ใช้
            # สำหรับ suction cup:
            self.robot.suck(close)
            
            # สำหรับ mechanical gripper อาจใช้:
            # self.robot.grip(close)
            
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"✗ ควบคุม gripper ล้มเหลว: {e}")
            return False
    
    def execute_grasp(self, grasp, depth_value: Optional[float] = None, 
                     confirm: bool = True) -> bool:
        """
        ทำการจับวัตถุตาม grasp ที่กำหนด
        
        Args:
            grasp: Grasp object จาก RuleBasedGraspGenerator
            depth_value: ค่า depth (ใช้คำนวณ Z) - optional
            confirm: ถามยืนยันก่อนทำ
            
        Returns:
            True ถ้าจับสำเร็จ
        """
        if not self.is_connected:
            print("✗ ยังไม่ได้เชื่อมต่อ robot")
            return False
        
        # แปลง pixel → robot coordinates
        cy, cx = grasp.center
        robot_x, robot_y = self.pixel_to_robot(cx, cy)
        
        # คำนวณ Z
        # TODO: ปรับตามการ calibrate depth-to-z ของจริง
        robot_z = self.grasp_height
        
        # คำนวณ rotation จาก grasp angle
        robot_r = np.degrees(grasp.angle)
        
        # แสดงข้อมูล
        print("\n" + "="*60)
        print("📍 ข้อมูลการจับวัตถุ")
        print("="*60)
        print(f"  Pixel coords:  ({cx:.0f}, {cy:.0f})")
        print(f"  Robot coords:  ({robot_x:.1f}, {robot_y:.1f}, {robot_z:.1f}) mm")
        print(f"  Grasp angle:   {robot_r:.1f}°")
        print(f"  Quality score: {grasp.quality:.3f}")
        print("="*60)
        
        # ขอยืนยัน
        if confirm:
            response = input("\n❓ ดำเนินการจับวัตถุ? (y/n): ")
            if response.lower() != 'y':
                print("❌ ยกเลิกการจับวัตถุ")
                return False
        
        try:
            print("\n🤖 เริ่มจับวัตถุ...")
            
            # ขั้นตอนที่ 1: เคลื่อนไปเหนือวัตถุ (safe height)
            print("  [1/7] เคลื่อนไปเหนือวัตถุ...")
            self.move_to(robot_x, robot_y, self.safe_height, robot_r)
            
            # ขั้นตอนที่ 2: เปิด gripper
            print("  [2/7] เปิด gripper...")
            self.control_gripper(close=False)
            
            # ขั้นตอนที่ 3: เคลื่อนลงไปจับ
            print("  [3/7] เคลื่อนลงไปจับวัตถุ...")
            self.move_to(robot_x, robot_y, robot_z, robot_r)
            
            # ขั้นตอนที่ 4: ปิด gripper (จับวัตถุ)
            print("  [4/7] จับวัตถุ...")
            self.control_gripper(close=True)
            time.sleep(0.5)
            
            # ขั้นตอนที่ 5: ยกวัตถุขึ้น
            print("  [5/7] ยกวัตถุขึ้น...")
            self.move_to(robot_x, robot_y, self.safe_height, robot_r)
            
            # ขั้นตอนที่ 6: เคลื่อนไปยังจุดวาง
            print("  [6/7] เคลื่อนไปยังจุดวาง...")
            drop_x, drop_y, drop_z, drop_r = self.drop_position
            self.move_to(drop_x, drop_y, drop_z, drop_r)
            
            # ขั้นตอนที่ 7: ปล่อยวัตถุ
            print("  [7/7] ปล่อยวัตถุ...")
            self.control_gripper(close=False)
            time.sleep(0.5)
            
            print("\n✅ จับวัตถุสำเร็จ!")
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️ ผู้ใช้หยุดการทำงาน!")
            self.emergency_stop()
            return False
            
        except Exception as e:
            print(f"\n✗ การจับวัตถุล้มเหลว: {e}")
            self.emergency_stop()
            return False
    
    def emergency_stop(self):
        """หยุดฉุกเฉิน"""
        print("\n🛑 EMERGENCY STOP!")
        if self.robot:
            try:
                # ปิด gripper ก่อน
                self.control_gripper(close=False)
                # หยุดการเคลื่อนไหว
                self.robot.close()
            except:
                pass
    
    def set_drop_position(self, x: float, y: float, z: float, r: float = 0):
        """กำหนดตำแหน่งวางวัตถุ"""
        self.drop_position = (x, y, z, r)
        print(f"ตั้งค่าจุดวางวัตถุ: ({x}, {y}, {z}, {r})")
    
    def set_heights(self, safe_height: float, grasp_height: float):
        """กำหนดความสูงในการจับ"""
        self.safe_height = safe_height
        self.grasp_height = grasp_height
        print(f"ตั้งค่าความสูง: safe={safe_height}mm, grasp={grasp_height}mm")
    
    def get_current_position(self) -> Optional[Tuple[float, float, float, float]]:
        """อ่านตำแหน่งปัจจุบัน"""
        if not self.is_connected:
            return None
        
        try:
            pose = self.robot.pose()
            return tuple(pose[:4])
        except:
            return None
    
    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        if self.is_connected and self.robot:
            try:
                self.robot.close()
                self.is_connected = False
                print("✓ ตัดการเชื่อมต่อแล้ว")
            except:
                pass
    
    def __del__(self):
        """Cleanup เมื่อ object ถูกทำลาย"""
        self.disconnect()
