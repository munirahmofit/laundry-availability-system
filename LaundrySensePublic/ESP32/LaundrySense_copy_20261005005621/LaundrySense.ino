#include <WiFi.h>
#include <FirebaseESP32.h>

// WIFI 
#define WIFI_SSID "Laundry"
#define WIFI_PASSWORD "********"

// FIREBASE 
#define FIREBASE_HOST "laundrysense**********************************"
#define FIREBASE_AUTH "***************************************"

// LAUNDRY CONFIG, change this per ESP32!
#define LAUNDRY_ID "LaundryB"
#define MACHINE_ID "Machine1"

// PINS
#define SENSOR_PIN 34
#define MOTOR_PIN  26
#define TOGGLE_PIN 27

// ---- SETTINGS ----
#define VIBRATION_THRESHOLD 10
#define STOP_DELAY          8000
#define WASH_DURATION       30000


FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

String lastStatus = "";
int vibrationCount = 0;
unsigned long lastVibrationTime = 0;
bool motorRunning = false;
unsigned long motorStartTime = 0;
int lastToggleState = HIGH;

void sendStatus(String status) {
  if (status != lastStatus) {
    String path = "/" + String(LAUNDRY_ID) + "/" + String(MACHINE_ID);
    if (Firebase.setString(fbdo, path + "/status", status)) {
      Serial.println("Status: " + status + " → Firebase ✓");
      lastStatus = status;
    } else {
      Serial.println("Firebase failed: " + fbdo.errorReason());
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_PIN, INPUT);
  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(TOGGLE_PIN, INPUT_PULLUP);
  digitalWrite(MOTOR_PIN, LOW);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi Connected!");

  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  Serial.println("Firebase Connected!");
}

void loop() {
  int toggleState = digitalRead(TOGGLE_PIN);

  if (lastToggleState == HIGH && toggleState == LOW && !motorRunning) {
    Serial.println("Toggle ON — Starting wash cycle!");
    digitalWrite(MOTOR_PIN, HIGH);
    motorRunning = true;
    motorStartTime = millis();
  }
  lastToggleState = toggleState;

  if (motorRunning && millis() - motorStartTime >= WASH_DURATION) {
    Serial.println("Wash cycle done — Motor OFF");
    digitalWrite(MOTOR_PIN, LOW);
    motorRunning = false;
  }

  int sensorValue = digitalRead(SENSOR_PIN);
  if (sensorValue == HIGH) {
    vibrationCount++;
    lastVibrationTime = millis();
  }

  if (vibrationCount >= VIBRATION_THRESHOLD) {
    sendStatus("In Use");
    vibrationCount = 0;
  }

  if (millis() - lastVibrationTime > STOP_DELAY && lastStatus == "In Use") {
    sendStatus("Available");
    vibrationCount = 0;
  }

  delay(50);
}




