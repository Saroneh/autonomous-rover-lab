# Module 2 — Opsummering (autonomous-rover-lab)

3D-simulation (Gazebo Harmonic) + **AUTO-mission** fra QGC-waypoints. Samme MAVLink-stack som Module 1; ny fysik, visning og missionsfiler.

**Forudsætning:** [module-1-summary.md](module-1-summary.md) (porte, venv, DroneKit, GUIDED).

**Gylden regel (uændret):** Python → MAVLink → ArduPilot → motorer. Gazebo viser kun verdenen; autopiloten styrer ud fra **GPS + mission**.

---

## 1. Module 1 vs Module 2

| | Module 1 | Module 2 |
|---|----------|----------|
| Fysik | Indbygget SITL (`-f rover`) | **Gazebo** + JSON-model (`gazebo-rover`) |
| Visning | MAVProxy 2D-kort | **Gazebo 3D** + kort |
| Terminaler | 2 | **3–4** |
| Navigation | `simple_goto` / `run_gps_route` (GUIDED) | **QGC `.waypoints` + AUTO** |
| Scripts | `run_hello.py`, `run_gps_route.py` | `run_mission.py`, `run_my_street.py` |
| Home | `sim/location.env` + `--custom-location` | Samme + **skal matche WP0** |

---

## 2. Arkitektur (udvidet)

```text
[Python / DroneKit]  ──UDP 14550──►  [MAVProxy]  ──TCP 5760──►  [ArduRover SITL]
                                                              │
                                                              │ JSON
                                                              ▼
                                                    [Gazebo + rover-model]
```

| Komponent | Rolle |
|-----------|--------|
| **Gazebo server** | Verden + fysik (uden GUI) |
| **Gazebo GUI** | 3D-visning |
| **SITL `gazebo-rover`** | Autopilot koblet til Gazebo-plugin (port 9002) |
| **Mission-fil** | Sekvens af GPS-punkter (QGC WPL 110) |
| **`run_mission.py`** | Upload mission → AUTO → arm → overvåg → HOLD/disarm |

---

## 3. Vigtige filer

| Sti | Formål |
|-----|--------|
| `sim/gazebo.env` | Stier til `ardupilot_gazebo`, `SITL_Models`, standard-verden |
| `sim/location.env` | Sim-home (lat, lon, alt, heading) = **waypoint 0** |
| `missions/*.waypoints` | Mission (QGC-format) |
| `scripts/gazebo_server.sh` | Terminal 1 — `gz sim -s` |
| `scripts/gazebo_gui.sh` | Terminal 2 — GUI |
| `scripts/start_sitl_gazebo.sh` | Terminal 3 — SITL + MAVProxy |
| `scripts/run_mission.py` | Terminal 4 — AUTO-mission |
| `scripts/run_my_street.py` | **Din** gaderute (kopi + tilpasning) |
| `config/rover-default.parm` | Reference (WP_RADIUS i **meter** på rover) |
| `docs/module-2-gazebo.md` | Opsætningsguide (én gang) |
| `docs/assignment-my-street-loop.md` | Trin-for-trin opgave (egen rute) |

---

## 4. Kørsel hver session

```bash
cd autonomous-rover-lab
source .venv/bin/activate   # altid — ellers mangler dronekit
```

| # | Kommando |
|---|----------|
| 1 | `./scripts/gazebo_server.sh` |
| 2 | `./scripts/gazebo_gui.sh` |
| 3 | `./scripts/start_sitl_gazebo.sh -w` (ved ny home / første gang) |
| 4 | `python scripts/run_mission.py` eller `python scripts/run_my_street.py` |

Stop alt: `./scripts/stop_sim.sh`

**Rækkefølge:** Gazebo **server** før SITL. Ved forkert home: `-w` på SITL (sletter EEPROM).

---

## 5. Kernebegreber (læringssti)

### 5.1 GUIDED vs AUTO

| Mode | Hvem bestemmer ruten | Typisk script |
|------|----------------------|---------------|
| **GUIDED** | Python sender ét punkt ad gangen (`simple_goto`) | `run_hello.py`, `run_gps_route.py` |
| **AUTO** | Mission i autopiloten (uploaded waypoints) | `run_mission.py`, `run_my_street.py` |

AUTO = “følg listen WP0 → WP1 → …”. Python starter/stopper og overvåger; autopiloten navigerer mellem punkterne.

### 5.2 Waypoint-fil (QGC WPL 110)

- **Rækkefølge = rute** (A→B→C→D→A). Ingen “gade”-viden — kun lat/lon.
- **WP0** = start/home → skal matche `sim/location.env`.
- **`frame=3`** = global, højde relativ til home.
- **`param2=5`** = accept-radius ca. 5 m (når tæt nok, næste WP).
- **WP4 = WP0** lukker loopet.

Meter på kortet (97 m, 37 m, …) bruges til **planlægning**; i filen står kun **koordinater**.

### 5.3 Sim vs rigtig gade (valg A / B)

| Valg | Sim | Rigtig vej senere |
|------|-----|-------------------|
| **A** (anbefalet først) | WP0 = fast demo-home; korte ben (~15–25 m) | Samme *format*, andre koordinater på hardware |
| **B** | WP0 = rigtige GPS; opdater `location.env` + `-w` | 1:1 med dit kvarter |

### 5.4 2D-kort vs Gazebo 3D

- Kortet: ofte **lige linjer** mellem waypoints.
- Gazebo: **skid-steer**, sving, overshoot → længere **kørt distance** end lige linje.
- Autopiloten følger **GPS**, øjet følger **modellen** — de kan divergere i sim.

### 5.5 AUTO stopper ikke og “kører tilbage”

- AUTO prøver **forlæns** at nå næste punkt (path following) — ikke “stop og bak”.
- Overshoot / forkert approach → **afstand til WP kan stige** selvom den “prøver”.
- **`closest so far`** i scriptet = korteste afstand til **aktivt** WP siden skift — måler **fremskridt**.
- Hvis afstand kun stiger → ingen reel tilnærmelse → script **stuck-abort** (sikkerhed).

### 5.6 Failsafes (sim vs virkelighed)

I sim er mange failsafes slakket (`ARMING_CHECK=0`, GCS failsafe off) for at lære.

Udendørs / drone: **geofence, RTL, batteri, GCS-link, RC override** — ellers kan et køretøj i princippet fortsætte indtil batteri/tom forbindelse. Samme stack, højere stakes i luften.

---

## 6. `run_mission.py` — hvad scriptet gør

1. Læser `.waypoints`
2. Tjekker afstand til WP0
3. Sætter `WP_RADIUS` / `WP_SPEED` (sim-venligt)
4. Uploader mission (DroneKit `wploader`)
5. Verificerer mission på board
6. AUTO + arm
7. Logger `active waypoint index` + afstand + `closest so far`
8. Afslutter ved sidste WP eller stuck-abort → HOLD + disarm

**Venv:** `source .venv/bin/activate` — system-`python` har ikke dronekit.

---

## 7. Typiske fejl og fixes

| Symptom | Sandsynlig årsag | Fix |
|---------|------------------|-----|
| Kører langt / stuck på WP1+ | `WP_RADIUS` for stor (fx 200 m), Gazebo/GPS desync | `param show WP_RADIUS` (2–5); fuld restart; `-w` |
| `closest so far` stiger | Overshoot, forkert ben, sim-sync | Restart stack; kortere ben; lavere hastighed |
| `Distance to WP0` stor | Home ≠ WP0 / gammel EEPROM | Match `location.env`; `start_sitl_gazebo.sh -w` |
| `got MISSION_ITEM` warning | DroneKit vs ArduPilot-quirk | Harmløs hvis upload OK |
| `ModuleNotFoundError: dronekit` | Ingen venv | `source .venv/bin/activate` |
| Mission upload timeout (INT) | Konflikt med DroneKit-tråd | Brug `commands.upload()` (som nu) |

---

## 8. Din gaderute-opgave (afslutning)

| Trin | Leverance |
|------|-----------|
| 1 | `missions/my_street_loop.waypoints`, `scripts/run_my_street.py` |
| 2 | Plan: 4 hjørner (dine meter: 97, 37, 71, 22) → sim-skala ~25 m ben |
| 3 | Koordinater i fil; WP0 = `location.env` |
| 5 | Default mission + docstring i `run_my_street.py` |
| 6 | Test i Gazebo (4 terminaler) |

**Læring:** Egen mission-fil + eget script-navn; forståelse af GPS-rækkefølge, accept-radius og sim-begrænsninger.

---

## 9. Module 2 — tjekliste (klar til Module 3)

- [ ] Kan starte/stoppe Gazebo + SITL + mission i rigtig rækkefølge
- [ ] Kan forklare GUIDED vs AUTO og QGC-waypoints
- [ ] Ved at WP0 = `location.env` og hvornår `-w` bruges
- [ ] Forstår `distance` vs `closest so far` og hvorfor AUTO ikke “bakker”
- [ ] Har `run_my_street.py` + `my_street_loop.waypoints`
- [ ] Ved at failsafes i sim ≠ udendørs konfiguration

---

## 10. Næste skridt (Module 3+)

| Emne | Formål |
|------|--------|
| QGroundControl | Tegn mission visuelt, export `.waypoints` |
| RTL / HOLD / failsafe i sim | Test “nødbremse” bevidst |
| Pi + UDP | Samme scripts, anden `--connect` |
| Geofence + `ARMING_CHECK` | Forberedelse til udendørs (Module 5) |
| Valg B på gaderute | Rigtige GPS på hardware |

---

## 11. Mental model (samlet)

```text
Mission-fil (lat/lon liste)
        ↓ upload
   ArduPilot AUTO  ←── GPS-position
        ↓
   Motor/kørsel  ←── Gazebo (sim) eller hjul (hardware)
```

Python er **operatør**: upload, arm, overvåg, stop — ikke bilens “hjernes GPS-navigation” under AUTO.

---

*autonomous-rover-lab · Module 2 + gaderute-opgave · 2026*
