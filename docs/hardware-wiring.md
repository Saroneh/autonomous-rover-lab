# Hardware wiring (Modules 3–4)

> **Safety:** No autonomous arming until RC e-stop is tested. First motor tests with wheels off the ground.

## Open decisions (Session A)

Record your answers here before Module 4:

| Question | Your answer |
|----------|-------------|
| Steering type | ☐ Skid (dual drive) ☐ Ackermann (servo steer) ☐ Pedal + wheel |
| Battery voltage | ☐ 12V ☐ 24V |
| Pixhawk model | |
| Pi model + mount | ☐ UART TELEM2 ☐ USB `/dev/ttyACM0` |

## Planned signal path

```
Pixhawk (ArduRover) ──MAIN OUT──► ESC or H-bridge (throttle / drive)
                 └──AUX OUT────► Steering servo (if ackermann)
GPS + compass ──► GPS1, COMPASS
Pi ──TELEM2/UART──► MAVProxy ──UDP 14550──► DroneKit (same as SITL)
RC receiver ─────► RC IN (manual + estop)
```

## Module 4 checklist

- [ ] `FRAME_TYPE` and `SERVOx_FUNCTION` match mechanics
- [ ] PWM/PPM calibration in Mission Planner
- [ ] RC override drive before autonomy
- [ ] Geofence + `ARMING_CHECK` enabled for outdoor (Module 5)

See `hardware/bill-of-materials.md` for parts list.
