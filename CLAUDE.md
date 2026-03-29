# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Automated drug dispenser for GE1354 university course. IoT system with embedded firmware, network bridge, and web management UI.

## Architecture

- **Micro:bit #1** (MicroPython): Sensor node — DHT20 (I2C 0x38), OLED SSD1306 (I2C 0x3C), passive buzzer (PWM pin1), serial to ESP32
- **Micro:bit #2** (MicroPython): Actuation node — servo motors for dispensing
- **ESP32** (Arduino C++): WiFi bridge, MQTT client, serial to Micro:bit #1
- **Web server** (Python): Hosts management UI, MQTT bridge, reverse-proxied
- **MQTT server**: External broker between ESP32 and web server

Data flow: DHT20 → Micro:bit #1 → ESP32 → MQTT → Web Server → Browser. Commands flow in reverse.

## Repository Layout

- `microbit/experiments/` — Small standalone test projects for individual components
- `microbit/main/` — Final integrated Micro:bit code (not yet created)
- `esp32/` — ESP32 Arduino firmware (not yet started)
- `server/` — Python web server + MQTT bridge (not yet started)
- `docs/` — Architecture and hardware documentation

## Development Notes

- Micro:bit code uses the `microbit` MicroPython module (i2c, pins, sleep, music). No pip/package manager — files are flashed directly.
- No build system, test framework, or linting is configured yet.
- Each experiment in `microbit/experiments/` is a self-contained project with its own `main.py` and driver modules.
- The project follows an incremental approach: build small experiments first, then integrate into `microbit/main/`.
