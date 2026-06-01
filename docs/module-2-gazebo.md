# Module 2 — Gazebo + waypoint mission

**Goal:** 3D simulation + autonomous square route via DroneKit `AUTO` mode.

## One-time setup (Session A)

### 1. ArduPilot Gazebo plugin

```bash
brew update
brew install rapidjson opencv gstreamer

export GZ_VERSION=harmonic
git clone https://github.com/ArduPilot/ardupilot_gazebo.git ~/ardupilot_gazebo
cd ~/ardupilot_gazebo
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
make -j4
```

Edit `sim/gazebo.env` if you cloned somewhere other than `~/ardupilot_gazebo`.

### 2. Rover worlds and models (recommended)

```bash
git clone https://github.com/ArduPilot/SITL_Models.git ~/SITL_Models
```

Default world `r1_rover_runway.sdf` includes an **R1 rover** with ArduPilot plugin (port 9002).

Alternative: `rover_playpen.sdf` (driveway-like obstacles; may download Fuel models on first run).

### 3. Align mission home

Set `sim/location.env` to match **waypoint 0** in `missions/driveway_square.waypoints` (or regenerate the mission file for your GPS area).

---

## Three-terminal workflow (every session)

### Terminal 1 — Gazebo server

```bash
cd autonomous-rover-lab
source .venv/bin/activate
./scripts/gazebo_server.sh
```

Wait until the world is loaded (server running, no crash).

### Terminal 2 — Gazebo GUI

```bash
cd autonomous-rover-lab
source .venv/bin/activate
./scripts/gazebo_gui.sh
```

You should see the 3D world and rover.

### Terminal 3 — SITL + MAVProxy

```bash
cd autonomous-rover-lab
source .venv/bin/activate
./scripts/start_sitl_gazebo.sh -w
```

Wait for heartbeat. First time: `-w` wipes EEPROM so home matches `location.env`.

### Terminal 4 — Mission (Session B)

```bash
cd autonomous-rover-lab
source .venv/bin/activate
python scripts/run_mission.py --mission missions/driveway_square.waypoints
```

Rover should arm in **AUTO**, follow the square, then HOLD/disarm.

---

## Stop everything

```bash
./scripts/stop_sim.sh
```

---

## Module 1 vs Module 2

| | Module 1 | Module 2 |
|---|----------|----------|
| Physics | Built-in SITL `rover` frame | Gazebo + JSON |
| View | MAVProxy 2D map | Gazebo 3D + map |
| Terminals | 2 | 3–4 |
| Navigation | `simple_goto` / route script | QGC waypoints + `AUTO` |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Gazebo empty / no rover | Use `r1_rover_runway.sdf`; ensure `SITL_Models` in `sim/gazebo.env` |
| SITL does not connect to Gazebo | Start **server** before `start_sitl_gazebo.sh`; check `ardupilot_gazebo` built |
| Mission “too far from WP0” | Match `location.env` and `driveway_square.waypoints`; use `-w` |
| Rover drives far / never finishes square | Stuck on WP1: increase `WP_RADIUS`, use `param2=5` in `.waypoints`, re-run mission script. Gazebo GUI **path length** can be ≫ straight-line distance (skid-steer weaving). Stop: `mode HOLD` in MAVProxy |
| Stuck on WP3 at ~100–200 m | Mission advanced with **WP_RADIUS too large** (e.g. 200 m from old parm file) or Gazebo GPS desync. In MAVProxy: `param show WP_RADIUS` (want ~5). Full restart: `stop_sim.sh` → Gazebo → `start_sitl_gazebo.sh -w` → mission |
| `got MISSION_ITEM` warning | Harmless DroneKit/ArduPilot quirk; mission still works |
| `gz: command not found` | Install Gazebo Harmonic (`brew install gz-harmonic` or osrf tap) |
| Plugin errors | `export GZ_VERSION=harmonic`; rebuild `ardupilot_gazebo` |

---

## Success criteria (Module 2)

- [ ] Rover visible in Gazebo 3D
- [ ] SITL + MAVProxy connected (heartbeat)
- [ ] `run_mission.py` completes square in simulation
- [ ] Understand 3-terminal launch order

**Opsummering:** [module-2-summary.md](module-2-summary.md)
