# Bill of materials (draft)

## Core (Modules 3–5)

| Item | Purpose | Notes |
|------|---------|-------|
| Ride-on chassis | Platform | 12V or 24V — confirm before motor driver |
| Pixhawk (4 / Cube Orange / similar) | ArduRover autopilot | |
| Raspberry Pi 4/5 | Companion + DroneKit | TELEM2 UART recommended |
| u-blox GPS M8N/M9N | Position | Mount with clear sky view |
| RC TX/RX + estop | Manual + safety | Test before autonomy |

## Drive (Module 4 — depends on steering)

| Item | Skid steer | Ackermann |
|------|------------|-----------|
| Motor driver | 2× H-bridge or 2× VESC | 1× H-bridge / ESC |
| Steering | — | Servo + linkage |
| Battery | Ride-on SLA / LiFePO4 | Match driver voltage |

## Optional (Module 6+)

| Item | Purpose |
|------|---------|
| Pi camera | Line follow / logging |
| Ultrasonic / LiDAR | Proximity stop |
| Rangefinder (Pixhawk) | `AVOID_ENABLE` |

## Software (Module 1 — no hardware)

- macOS or Linux dev machine
- Python 3.9 + packages in `requirements.txt`
- ArduPilot submodule (SITL build)

Cost and vendor links: fill in during Module 7 business validation.
