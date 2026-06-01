# Opgave: Din egen gaderute (~4 GPS-hjørner)

**Mål:** En mission-fil + dit eget script, der kører en firkant/rute omkring en “gade” i sim (senere samme fil til rigtig GPS).

**Leverancer:**

| Fil | Formål |
|-----|--------|
| `missions/my_street_loop.waypoints` | 4 hjørner + tilbage til start (5–6 punkter) |
| `scripts/run_my_street.py` | Dit script (baseret på `run_mission.py`) |
| `sim/location.env` | WP0 = sim-home (kun hvis du flytter start) |

**Sim vs. rigtig vej:** I Gazebo/SITL skal **waypoint 0** matche `sim/location.env`. Du kan godt *navngive* ruten efter din rigtige gade og bruge **samme form** (4 hjørner), men koordinaterne i sim er ofte “Danmark-demo” eller små offset fra home (~20–50 m per ben) indtil du kører hardware udendørs.

---

## Trinoversigt (godkend ét ad gangen)

| Trin | Du laver | Godkendelse |
|------|----------|-------------|
| **1** | Kopier skabelon-filer | Filnavne findes, ingen ændring i logik endnu |
| **2** | Tegn ruten (4 hjørner på kort) | Skitse + ca. meter mellem hjørner |
| **3** | Udfyld `.waypoints` | 5–6 linjer, korrekt QGC-format |
| **4** | Opdater `location.env` (hvis ny WP0) | `Distance to WP0` ≈ 0 m ved start |
| **5** | Tilpas script (default mission + docstring) | Script peger på din fil |
| **6** | Tør kørsel (kun SITL eller Gazebo) | Mission fuldføres eller du kan forklare fejl |
| **7** | Dokumentér (5–10 linjer i denne fil) | Hvad du lærte |

---

## Trin 1 — Kopier skabelonen (START HER)

Kør fra repo-roden:

```bash
cd /Users/danialsaroneh/Documents/autonomous-rover-lab
cp missions/driveway_square.waypoints missions/my_street_loop.waypoints
cp scripts/run_mission.py scripts/run_my_street.py
```

**Tjekliste før du siger “trin 1 færdig”:**

- [ ] `missions/my_street_loop.waypoints` findes
- [ ] `scripts/run_my_street.py` findes
- [ ] Du har **ikke** slettet `driveway_square` / `run_mission.py`

**Valgfrit (anbefalet):** Gør scriptet eksekverbart:

```bash
chmod +x scripts/run_my_street.py
```

---

## Trin 2 — Kortlæg din “gade” (kommer efter godkendelse af trin 1)

1. Åbn Google Maps (eller QGroundControl planlægger).
2. Markér **4 hjørner** rundt om en blok / vejstrækning.
3. Notér i notes:
   - Hjørne A, B, C, D (klokken rundt)
   - Ca. afstand A→B, B→C, … i meter
4. **Sim-beslutning:**  
   - **A)** Behold nuværende `location.env` og flyt kun WP1–4 ~15–30 m væk fra WP0 (nemmest).  
   - **B)** Sæt WP0 til rigtige GPS fra dit kvarter og opdater `location.env` + `start_sitl_gazebo.sh -w`.

---

## Trin 3 — Rediger waypoints (efter trin 2)

Format (én linje per punkt, tab-separeret):

```
QGC WPL 110
0	1	3	16	0	5	0	0	<lat0>	<lon0>	0	1
1	0	3	16	0	5	0	0	<lat1>	<lon1>	0	1
...
```

Regler:

- **WP0:** `current=1`, samme lat/lon som `ROVER_HOME_*` i `location.env`
- **WP1–3:** dine tre andre hjørner
- **WP4:** tilbage til start (samme som WP0) — lukker loopet
- **frame=3**, **param2=5** (accept-radius 5 m) — kopier fra skabelon

---

## Trin 4 — `location.env` (kun hvis du flyttede start)

Opdater `sim/location.env` så den matcher WP0. Genstart sim med:

```bash
./scripts/start_sitl_gazebo.sh -w
```

---

## Trin 5 — Tilpas `run_my_street.py`

Minimum:

1. Øverst i docstring: dit gadenavn / formål.
2. Default `--mission` → `missions/my_street_loop.waypoints`

Find linjen med `default="missions/driveway_square.waypoints"` og skift filnavn.

Kør senere:

```bash
python scripts/run_my_street.py
# eller eksplicit:
python scripts/run_my_street.py --mission missions/my_street_loop.waypoints
```

---

## Trin 6 — Test i sim

Samme rækkefølge som Module 2:

1. `./scripts/gazebo_server.sh`
2. `./scripts/gazebo_gui.sh`
3. `./scripts/start_sitl_gazebo.sh -w`
4. `python scripts/run_my_street.py`

I MAVProxy undervejs: `wp list`, `param show WP_RADIUS`.

---

## Trin 7 — Kort refleksion (dig)

Udfyld nederst i denne fil:

- Hvilke koordinater brugte du (sim eller rigtig gade)?
- GUIDED vs AUTO — hvorfor mission-fil?
- Én fejl du havde og hvordan du fixede den.

---

*Status: trin ___ / 7 · Godkendt af: ___*
