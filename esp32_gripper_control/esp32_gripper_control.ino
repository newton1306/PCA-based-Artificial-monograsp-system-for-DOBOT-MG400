#include <Arduino.h>
#include <ESP32Servo.h>

// =================================================================
// ESP32 Servo Gripper Controller
// สำหรับใช้กับ 4.1_dynamic_gripper_detection.ipynb
// =================================================================

// Servo Configuration
Servo myServo1;  // นิ้วซ้าย  - GPIO 12
Servo myServo2;  // นิ้วขวา  - GPIO 13

const int SERVO_PIN_1 = 12;
const int SERVO_PIN_2 = 13;

const int ANGLE_OPEN = 22;   // กางแขนออกสุด (74mm)
const int ANGLE_CLOSE = 96;  // หุบแขนเข้าสุด (5mm)
int currentAngle = ANGLE_OPEN;

// =================================================================
// Setup
// =================================================================
void setup() {
  Serial.begin(115200);
  
  // Initialize Servos
  myServo1.attach(SERVO_PIN_1);
  myServo2.attach(SERVO_PIN_2);
  moveToAngle(ANGLE_OPEN);
  
  Serial.println("=================================");
  Serial.println("ESP32 Gripper Controller");
  Serial.println("For 4.1_dynamic_gripper_detection");
  Serial.println("=================================");
  Serial.println("Commands:");
  Serial.println("  O     = Open gripper fully (22°)");
  Serial.println("  C     = Close gripper fully (96°)");
  Serial.println("  G<n>  = Move to angle n (22-96)");
  Serial.println("  ?     = Get current angle");
  Serial.println("=================================");
}

// =================================================================
// Servo Functions
// =================================================================
void moveToAngle(int targetAngle) {
  targetAngle = constrain(targetAngle, ANGLE_OPEN, ANGLE_CLOSE);
  
  // Smooth movement
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
// Main Loop
// =================================================================
void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() == 0) return;
    
    char command = input.charAt(0);
    
    // === Open Gripper ===
    if (command == 'O' || command == 'o') {
      Serial.println("Opening gripper...");
      moveToAngle(ANGLE_OPEN);
      Serial.print("OK:OPEN:");
      Serial.println(currentAngle);
    }
    // === Close Gripper ===
    else if (command == 'C' || command == 'c') {
      Serial.println("Closing gripper...");
      moveToAngle(ANGLE_CLOSE);
      Serial.print("OK:CLOSE:");
      Serial.println(currentAngle);
    }
    // === Go to specific angle ===
    else if (command == 'G' || command == 'g') {
      if (input.length() > 1) {
        int targetAngle = input.substring(1).toInt();
        Serial.print("Moving to angle: ");
        Serial.println(targetAngle);
        moveToAngle(targetAngle);
        Serial.print("OK:GRIP:");
        Serial.println(currentAngle);
      } else {
        Serial.println("ERR:No angle specified");
      }
    }
    // === Status ===
    else if (command == '?') {
      Serial.print("ANGLE:");
      Serial.println(currentAngle);
    }
    // === Unknown command ===
    else {
      Serial.print("ERR:Unknown '");
      Serial.print(command);
      Serial.println("'");
    }
  }
}
