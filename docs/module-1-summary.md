# Module 1 — Opsummering (autonomous-rover-lab)

Digitalt laboratorium: styre en virtuel rover med Python via samme stack som senere bruges med Pixhawk.

**Gylden regel:** Python taler aldrig direkte med motorer. Alt går gennem **MAVLink → ArduPilot**.

---

## 1. Arkitektur og porte

### Dataflow

```text
[Python / DroneKit]  ──MAVLink──►  [MAVProxy]  ──MAVLink──►  [ArduRover SITL]
        UDP 14550                        TCP 5760
```

### Komponenter

| Komponent | Rolle |
|-----------|--------|
| **ArduRover SITL** | Virtuel autopilot; simulerer roveren |
| **MAVProxy** | Ground station + relay; kort/konsol; skal forblive forbundet |
| **DroneKit-scripts** | Dine missioner (`run_hello.py`, `run_gps_route.py`) |

### Porte

| Port | Protokol | Hvem lytter | Hvem forbinder |
|------|----------|-------------|----------------|
| **5760** | TCP | ArduRover SITL | MAVProxy (master) |
| **14550** | UDP | MAVProxy (output) | DroneKit, QGroundControl, m.fl. |

**Hvorfor MAVProxy er påkrævet:** SITL venter ofte på en GCS på TCP 5760. Uden forbindelse kan sim hænge. MAVProxy forbinder 5760 ↔ 14550 og giver kort/konsol.

---

## 2. Repo og værktøjskæde

| Emne | Detalje |
|------|---------|
| **Python** | Kun **3.9** (`dronekit==2.9.2` virker ikke på 3.10+) |
| **Virtuelt miljø** | `.venv` — alle pip-pakker her |
| **ardupilot/** | Git **submodule** (stor; ikke kopieret i hvert push) |
| **Init submodule** | `git submodule update --init --recursive` |
| **Byg SITL** | `cd ardupilot && ./waf configure --board sitl && ./waf rover` |

---

## 3. Kørsel hver session

### Terminal 1 — simulation

```bash
cd autonomous-rover-lab
source .venv/bin/activate
./scripts/start_sitl.sh
```

Ved forkert/gammel home-position:

```bash
./scripts/start_sitl.sh -w
```

(`-w` sletter EEPROM, så gammel home i `eeprom.bin` ikke overskriver `sim/location.env`.)

### Terminal 2 — Python

```bash
source .venv/bin/activate
python scripts/run_hello.py
```

Eller GPS-rute:

```bash
python scripts/run_gps_route.py \
  --connect 127.0.0.1:14550 \
  --from-lat <start_lat> --from-lon <start_lon> \
  --to-lat <dest_lat> --to-lon <dest_lon>
```

### Stop

```bash
./scripts/stop_sim.sh
```

---

## 4. SITL-start og hjemmeposition

| Flag / fil | Betydning |
|------------|-----------|
| **`-v Rover`** | Køretøjstype = ArduRover |
| **`-f rover`** | SITL-frame (indbygget rover-fysik) |
| **`--console --map`** | MAVProxy GUI ved opstart |
| **`--custom-location LAT,LON,ALT,HEADING`** | Spawn/home (ikke `--home` på denne ArduPilot-version) |
| **`sim/location.env`** | `ROVER_HOME_LAT`, `ROVER_HOME_LNG`, `ROVER_HOME_ALT`, `ROVER_HOME_HEADING` |
| **`start_sitl.sh`** | Læser `location.env` og sender `--custom-location` automatisk |
| **`-w`** | Wipe EEPROM ved opstart |

Eksempel `sim/location.env`:

```bash
ROVER_HOME_LAT=55.745364
ROVER_HOME_LNG=12.480541
ROVER_HOME_ALT=0
ROVER_HOME_HEADING=0
```

---

## 5. DroneKit-mønster

| Trin | Handling |
|------|----------|
| 1 | `connect('127.0.0.1:14550', wait_ready=True)` |
| 2 | `vehicle.mode = VehicleMode('GUIDED')` |
| 3 | `vehicle.armed = True` (vent til arm) |
| 4 | `vehicle.simple_goto(LocationGlobalRelative(lat, lon, alt))` |
| 5 | Vent til mål (afstand / timeout) |
| 6 | `VehicleMode('HOLD')` → disarm |

**Vigtigt:** Brug **`lon`**, ikke `lng`, i `LocationGlobalRelative`.

---

## 6. Scripts i projektet

| Script | Formål |
|--------|--------|
| `scripts/setup_rover.sh` | PATH, venv, ArduPilot tools |
| `scripts/start_sitl.sh` | SITL + MAVProxy + custom home |
| `scripts/stop_sim.sh` | Stop SITL / MAVProxy |
| `scripts/diag_rover.sh` | Tjek venv, build, porte |
| `scripts/run_hello.py` | ~5 m frem, disarm |
| `scripts/run_gps_route.py` | Kør fra ét GPS-punkt til et andet |

---

## 7. MAVProxy kort/konsol (afhængigheder)

Installer i **samme `.venv`** som kører MAVProxy:

| Pakke | Bruges til |
|-------|------------|
| `pillow` | MAVProxy map |
| `opencv-python` | `cv2` i map-modul |
| `matplotlib` | Ikoner / map UI |
| `wxpython` | Ofte påkrævet til `console`-modul |

I MAVProxy-prompt (hvis ikke auto-loadet):

```text
module load map
module load console
```

---

## 8. Typiske fejl og løsninger

| Problem | Årsag | Løsning |
|---------|--------|---------|
| `Operation not permitted` i Documents | macOS privacy | Giv Terminal adgang til Documents / Full Disk Access |
| Ingen `ardupilot/` mappe | Submodule ikke hentet | `git submodule update --init --recursive` |
| `No module named 'map'` / `cv2` / `matplotlib` | Manglende GUI-deps | `pip install` i `.venv` (se tabel ovenfor) |
| Route: "too far from start" (fx 166 m) | SITL home ≠ `--from-*` | Opdater `sim/location.env`; `start_sitl.sh -w` |
| Kort viser forkert område | Gammel home eller zoom | Ret `location.env`, `-w`, zoom/pan i map |
| `AttributeError: 'lng'` | DroneKit bruger `lon` | Ret til `start.lon` / `target.lon` |

---

## 9. Hvad Module 1 *ikke* er

| Module 1 | Module 2+ |
|----------|-----------|
| Kun SITL + MAVProxy 2D-kort | Gazebo Harmonic (3D verden) |
| 2 terminaler | 3+ terminaler (gz server, gz GUI, SITL) |
| `simple_goto` / enkelt rute-script | Waypoint-filer + `run_mission.py` |
| Ingen rigtig hardware | Pixhawk, Pi, motorer (senere moduler) |

---

## 10. Sikkerhed (hardware — senere moduler)

| Regel | Hvornår |
|-------|---------|
| Test **RC + nødstop** før autonomi | Module 4+ |
| Første motortest med **hjul i luften** | Module 4 |
| Fornuftig **geofence** og **ARMING_CHECK** udendørs | Module 5 |

---

## 11. Module 1 — tjekliste (klar til Module 2)

- [ ] Kan tegne: Python → **14550** → MAVProxy → **5760** → SITL
- [ ] Ved hvorfor MAVProxy skal køre sammen med SITL
- [ ] Kan skelne `start_sitl.sh` vs. `run_hello.py` / `run_gps_route.py`
- [ ] Forstår `sim/location.env`, `--custom-location` og `-w`
- [ ] Kan bruge GUIDED + `simple_goto` med **`lat` / `lon`**
- [ ] Ved hvorfor rute-script afviste ved forkert startposition

---

## 12. Næste skridt — Module 2

**Fuldt opslag:** [module-2-summary.md](module-2-summary.md)

| Leverance | Beskrivelse |
|-----------|-------------|
| Gazebo-verden | Harmonic + `ardupilot_gazebo` + `SITL_Models` |
| Mission | `missions/driveway_square.waypoints` (+ din `my_street_loop`) |
| Script | `run_mission.py`, `run_my_street.py` — AUTO via DroneKit |
| Workflow | 4 terminaler: Gazebo server/GUI → SITL → mission |

Samme mentale model; du tilføjer **3D-visualisering** og **missionsfiler**.

---

*Genereret til autonomous-rover-lab · Module 1*
