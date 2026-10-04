# LaundrySense – IoT-Based Laundry Availability System

LaundrySense is an IoT-based system developed as a Final Year Project (FYP) to monitor the availability of washing machines in BSP area.

## Project Overview

The system uses an ESP32 and vibration sensor to detect whether a washing machine is currently being used. The detected status is sent to Firebase Realtime Database and displayed on a web dashboard.

The system also provides Telegram notifications for the laundry owner when certain maintenance conditions are detected.

## Technologies Used

- ESP32
- SW-420 Vibration Sensor
- Arduino IDE
- HTML
- CSS
- JavaScript
- Firebase Realtime Database
- Python
- Telegram Bot
- Leaflet.js

## System Flow

Vibration Sensor → ESP32 → Wi-Fi → Firebase → Web Dashboard

## Main Features

- Real-time laundry machine availability monitoring
- Washing machine and dryer status detection
- Web-based dashboard
- Firebase real-time database integration
- Telegram notification for maintenance monitoring

## Project Structure

```text
ESP32/
└── LaundrySense.ino

Web Dashboard/
├── 404.html
├── bot.py
├── firebase.json
└── index.html
