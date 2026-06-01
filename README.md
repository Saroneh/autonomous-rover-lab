# autonomous-rover-lab

Autonomous rover built from an electric ride-on children's car, using the same **MAVLink → ArduPilot → motors** stack as a typical ArduPilot multirotor project: SITL, MAVProxy, DroneKit-Python, later Gazebo and a Raspberry Pi companion.

**Module 1 goal:** ArduRover SITL only (no Gazebo). Virtual rover drives ~5 m on a DroneKit command.

## Architecture

```
[Python / DroneKit]  ←MAVLink→  [MAVProxy]  ←→  [ArduRover SITL or Pixhawk]
```

Python never talks to motors directly.

## Repo layout

```
autonomous-rover-lab/
├── README.md
├── requirements.txt          # Python 3.9 pins
├── .venv/
├── ardupilot/                # git submodule
├── config/rover-default.parm
├── missions/*.waypoints
├── scripts/
│   ├── setup_rover.sh
│   ├── start_sitl.sh
│   ├── stop_sim.sh
│   ├── diag_rover.sh
│   └── run_hello.py
├── sim/                      # Module 2+ (Gazebo)
└── docs/
```

## Prerequisites

- **macOS** (tested path) or Linux
- **Python 3.9** only (`dronekit==2.9.2` breaks on 3.10+)
- Homebrew Python 3.9: `/opt/homebrew/bin/python3.9`

## One-time setup

```bash
cd autonomous-rover-lab

# Python environment
/opt/homebrew/bin/python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# ArduPilot submodule + SITL build
git submodule update --init --recursive
cd ardupilot
Tools/environment_install/install-prereqs-mac.sh -y   # macOS; see ArduPilot docs for Linux
./waf configure --board sitl
./waf rover
cd ..

# Verify
./scripts/diag_rover.sh
```

## Module 1 — run SITL + DroneKit hello

**Terminal 1** — SITL + MAVProxy (do not skip MAVProxy; SITL blocks on TCP 5760 without a GCS):

```bash
source .venv/bin/activate
./scripts/start_sitl.sh
```

Wait for heartbeat. Useful MAVProxy checks:

```
status
mode guided
arm throttle
```

**Terminal 2** — drive 5 m forward:

```bash
source .venv/bin/activate
python scripts/run_hello.py
```

**Stop simulation:**

```bash
./scripts/stop_sim.sh
```

### Success criteria (Module 1)

- [ ] Explain: Python → MAVLink → ArduRover → motors (sim)
- [ ] SITL rover moves ~5 m on `run_hello.py`
- [ ] Same workflow: venv → `sim_vehicle` → MAVProxy → DroneKit
- [ ] Repo ready for Module 2 (Gazebo) without restructuring

## Module 2 — Gazebo + waypoint square

Full guide: **[docs/module-2-gazebo.md](docs/module-2-gazebo.md)** (one-time `ardupilot_gazebo` + `SITL_Models` setup).  
Summary: **[docs/module-2-summary.md](docs/module-2-summary.md)** (core concepts + gaderute-opgave).

**Terminal 1** — Gazebo server:

```bash
./scripts/gazebo_server.sh
```

**Terminal 2** — Gazebo GUI:

```bash
./scripts/gazebo_gui.sh
```

**Terminal 3** — SITL for Gazebo:

```bash
./scripts/start_sitl_gazebo.sh -w
```

**Terminal 4** — AUTO mission:

```bash
python scripts/run_mission.py --mission missions/driveway_square.waypoints
```

## Module roadmap

| Module | Focus |
|--------|--------|
| 1 | SITL + DroneKit hello (this) |
| 2 | Gazebo Harmonic + waypoint square |
| 3 | Pixhawk + Pi (heartbeat, no motors) |
| 4 | Mechanical integration + RC test |
| 5 | Outdoor GPS autonomy |
| 6 | Vision / proximity |
| 7 | Demo + business one-pager |

See `docs/drone-parity.md` for what transfers between vehicle types.

## Configuration

- Default params: `config/rover-default.parm` (set `FRAME_TYPE` when steering type is known)
- Sample mission: `missions/driveway_test.waypoints` (Module 5)

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| SITL hangs at startup | Ensure MAVProxy is running (`start_sitl.sh` includes `--console --map`) |
| DroneKit cannot connect | Connect to `127.0.0.1:14550` (MAVProxy UDP out), not 5760 |
| `arm` fails in SITL | Wait for GPS/EKF; or use params in `rover-default.parm` for sim |
| Wrong Python | `python -c 'import sys; print(sys.version_info[:2])'` must be `(3, 9)` |

```bash
./scripts/diag_rover.sh
```

## License

ArduPilot submodule is GPLv3. Project scripts/docs: use as you wish for your lab.
