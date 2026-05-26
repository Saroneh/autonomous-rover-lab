# Drone ↔ Rover transfer matrix

This repo is **standalone** — no symlinks or shared paths with other projects. The table below tracks which **skills and assets** transfer when you switch vehicle type later.

| Skill / asset | Rover (this repo) | Multirotor later |
|---------------|-------------------|------------------|
| ArduPilot params & missions | ArduRover | ArduCopter |
| MAVLink / MAVProxy | identical | identical |
| DroneKit scripts | ✓ (modes differ) | ✓ |
| `sim_vehicle.py` workflow | `-v Rover` | `-v ArduCopter` |
| Waypoint files | same QGC format | same |
| Gazebo Harmonic macOS | simpler world (Module 2) | iris + JSON plugin |
| Pi companion computer | ✓ | ✓ |
| GPS + EKF | ✓ | ✓ |
| Vision on Pi | easier on ground | reuse concepts |

## Rover-specific shortcuts (document when used)

| Topic | Rover choice | Notes |
|-------|--------------|-------|
| Simulation Phase A | Pure SITL, `-f rover` | No Gazebo until Module 2 |
| Simulation Phase B | Gazebo flat world | Skip `ardupilot_gazebo` JSON until needed |
| Steering | TBD: skid vs ackermann | Set `FRAME_TYPE` in `config/rover-default.parm` |
| Arm checks | `ARMING_CHECK=0` in SITL | Restore for outdoor (Module 5) |

## Mental model (unchanged)

```
[Python / DroneKit]  ←MAVLink→  [MAVProxy optional]  ←→  [ArduPilot]
                                        ↑
                          [SITL dev] or [Pi UART/UDP field]
                                        ↓
                              [Motors + steering + GPS]
```

Python never drives motors directly — only MAVLink to the autopilot.

## When to update this file

- Choosing skid vs ackermann vs separate throttle/steer
- Changing default connect string (SITL vs Pi)
- Adding Gazebo or skipping it
- Any param shortcut taken for sim that must be reverted for hardware
