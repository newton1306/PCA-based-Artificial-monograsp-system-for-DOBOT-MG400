#include <Arduino.h>
#include <ESP32Servo.h>

// =================================================================
// ESP32 Servo Gripper + TF-Luna LIDAR v11
// สำหรับใช้กับ 11_lidar_grasp_v11.ipynb
// =================================================================
//
// 🔌 WIRING TF-Luna V1.3 (6 สาย) → ESP32:
//
//   ลำดับ  สี       Pin        ต่อกับ ESP32
//   ─────────────────────────────────────────
//     1    แดง      VIN        5V
//     2    ดำ       RXD        GPIO17 (TX2)
//     3    เหลือง   TXD        GPIO16 (RX2)
//     4    เขียว    GND        GND
//     5    น้ำเงิน  Mode       ลอยไว้ หรือ 3.3V (UART mode)
//     6    ขาว      OUT        ไม่ต้องต่อ
//
// ⚠️ สำคัญ: สายน้ำเงิน (Mode) ต้องลอยไว้ หรือต่อ 3.3V
//           ถ้าต่อ GND จะเป็น I2C mode และไม่ทำงาน!
//
// 🔌 SERVO:
//   Servo1 (นิ้วซ้าย)  → GPIO12
//   Servo2 (นิ้วขวา)   → GPIO13
//
// =================================================================

// ==================== SERVO CONFIG ====================
Servo myServo1;
Servo myServo2;

const int SERVO_PIN_1 = 12;
const int SERVO_PIN_2 = 13;
const int ANGLE_OPEN = 22;
const int ANGLE_CLOSE = 96;
int currentAngle = ANGLE_OPEN;

// ==================== TF-LUNA LIDAR ====================
// ดำ (RXD) → GPIO17 (ESP32 TX2)
// เหลือง (TXD) → GPIO16 (ESP32 RX2)

#define LIDAR_RX 16  // ESP32 RX2 ← TF-Luna TXD (เหลือง)
#define LIDAR_TX 17  // ESP32 TX2 → TF-Luna RXD (ดำ)

HardwareSerial LidarSerial(2);

int lidarDistance = 0;
int lidarStrength = 0;

// =================================================================
// Setup
// =================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // TF-Luna UART: 115200, 8N1
  LidarSerial.begin(115200, SERIAL_8N1, LIDAR_RX, LIDAR_TX);
  
  // Servos
  myServo1.attach(SERVO_PIN_1);
  myServo2.attach(SERVO_PIN_2);
  moveToAngle(ANGLE_OPEN);
  
  Serial.println("");
  Serial.println("=========================================");
  Serial.println("ESP32 + TF-Luna LIDAR v11");
  Serial.println("=========================================");
  Serial.println("");
  Serial.println("WIRING (TF-Luna V1.3 - 6 wires):");
  Serial.println("  1. RED    (VIN)  -> 5V");
  Serial.println("  2. BLACK  (RXD)  -> GPIO17");
  Serial.println("  3. YELLOW (TXD)  -> GPIO16");
  Serial.println("  4. GREEN  (GND)  -> GND");
  Serial.println("  5. BLUE   (Mode) -> FLOAT or 3.3V");
  Serial.println("  6. WHITE  (OUT)  -> Not connected");
  Serial.println("");
  Serial.println("Commands: L=LIDAR, O=Open, C=Close, G<n>=Angle");
  Serial.println("=========================================");
  
  // Test LIDAR on startup
  delay(500);
  Serial.println("\nTesting LIDAR...");
  if (readLidar()) {
    Serial.print("LIDAR OK! Distance: ");
    Serial.print(lidarDistance * 10);
    Serial.println(" mm");
  } else {
    Serial.println("LIDAR: No response");
    Serial.println("Check: Blue wire must be FLOATING (not GND)!");
  }
}

// =================================================================
// Servo Functions
// =================================================================
void moveToAngle(int targetAngle) {
  targetAngle = constrain(targetAngle, ANGLE_OPEN, ANGLE_CLOSE);
  
  if (currentAngle < targetAngle) {
    for (int angle = currentAngle; angle <= targetAngle; angle++) {
      myServo1.write(angle);
      myServo2.write(angle);
      delay(10);
    }
  } else {
    for (int angle = currentAngle; angle >= targetAngle; angle--) {
      myServo1.write(angle);
      myServo2.write(angle);
      delay(10);
    }
  }
  currentAngle = targetAngle;
}

// =================================================================
// TF-Luna LIDAR - Read Distance
// =================================================================
bool readLidar() {
  // TF-Luna sends 9-byte frames continuously at 100Hz
  // Frame: 0x59 0x59 Dist_L Dist_H Str_L Str_H Temp_L Temp_H Checksum
  
  // Clear any old data
  while (LidarSerial.available()) {
    LidarSerial.read();
  }
  
  // Wait for fresh data (max 200ms)
  unsigned long startTime = millis();
  while (LidarSerial.available() < 9) {
    if (millis() - startTime > 200) {
      return false;
    }
    delay(1);
  }
  
  // Search for header 0x59 0x59
  uint8_t buf[9];
  int maxAttempts = 100;
  
  for (int attempt = 0; attempt < maxAttempts; attempt++) {
    if (LidarSerial.available() < 2) {
      delay(5);
      continue;
    }
    
    buf[0] = LidarSerial.read();
    if (buf[0] != 0x59) continue;
    
    buf[1] = LidarSerial.read();
    if (buf[1] != 0x59) continue;
    
    // Found header! Read remaining 7 bytes
    startTime = millis();
    while (LidarSerial.available() < 7) {
      if (millis() - startTime > 50) return false;
      delay(1);
    }
    
    for (int i = 2; i < 9; i++) {
      buf[i] = LidarSerial.read();
    }
    
    // Verify checksum
    uint8_t checksum = 0;
    for (int i = 0; i < 8; i++) {
      checksum += buf[i];
    }
    
    if (checksum == buf[8]) {
      lidarDistance = buf[2] | (buf[3] << 8);  // cm
      lidarStrength = buf[4] | (buf[5] << 8);
      return true;
    }
  }
  
  return false;
}

// =================================================================
// Main Loop
// =================================================================
void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() == 0) return;
    
    char cmd = input.charAt(0);
    
    // Open Gripper
    if (cmd == 'O' || cmd == 'o') {
      moveToAngle(ANGLE_OPEN);
      Serial.print("OK:OPEN:");
      Serial.println(currentAngle);
    }
    // Close Gripper
    else if (cmd == 'C' || cmd == 'c') {
      moveToAngle(ANGLE_CLOSE);
      Serial.print("OK:CLOSE:");
      Serial.println(currentAngle);
    }
    // Gripper to angle
    else if (cmd == 'G' || cmd == 'g') {
      if (input.length() > 1) {
        int angle = input.substring(1).toInt();
        moveToAngle(angle);
        Serial.print("OK:GRIP:");
        Serial.println(currentAngle);
      }
    }
    // Read LIDAR
    else if (cmd == 'L' || cmd == 'l') {
      if (readLidar()) {
        // Return in mm
        Serial.print("LIDAR:");
        Serial.println(lidarDistance * 10);
      } else {
        Serial.println("LIDAR:ERR");
      }
    }
    // Status
    else if (cmd == '?') {
      Serial.print("ANGLE:");
      Serial.print(currentAngle);
      if (readLidar()) {
        Serial.print(" LIDAR:");
        Serial.print(lidarDistance * 10);
        Serial.print("mm STR:");
        Serial.println(lidarStrength);
      } else {
        Serial.println(" LIDAR:ERR");
      }
    }
    else {
      Serial.println("ERR:Unknown");
    }
  }
}
