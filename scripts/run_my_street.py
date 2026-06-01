#!/usr/bin/env python
"""
Min gaderute — AUTO mission omkring 4 hjørner (sim, valg A).
Mission: missions/my_street_loop.waypoints

Prerequisites:
  Gazebo + SITL running (start_sitl_gazebo.sh), heartbeat on MAVProxy.
  Waypoint home should match sim/location.env (first WP = home).

Usage:
  source .venv/bin/activate
  python scripts/run_my_street.py
  python scripts/run_my_street.py --mission missions/my_street_loop.waypoints
"""

from __future__ import print_function

import argparse
import math
import sys
import time

from dronekit import Command, VehicleMode, connect


def load_qgc_waypoints(path):
    """Parse QGroundControl WPL 110 file into DroneKit Command list."""
    commands = []
    with open(path, "r") as handle:
        lines = handle.readlines()

    if not lines or not lines[0].strip().startswith("QGC WPL"):
        raise ValueError("Not a QGC WPL file: {}".format(path))

    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 12:
            parts = line.split()
        if len(parts) < 12:
            raise ValueError("Bad waypoint line: {}".format(line))

        seq = int(parts[0])
        current = int(parts[1])
        frame = int(parts[2])
        command = int(parts[3])
        p1, p2, p3, p4 = (float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7]))
        lat, lon, alt = float(parts[8]), float(parts[9]), float(parts[10])
        autocontinue = int(parts[11])

        commands.append(
            Command(
                seq,
                0,
                0,
                frame,
                command,
                current,
                autocontinue,
                p1,
                p2,
                p3,
                p4,
                lat,
                lon,
                alt,
            )
        )
    return commands


def command_lat_lon(cmd):
    """DroneKit Command stores waypoint position as x=lat, y=lon, z=alt."""
    return float(cmd.x), float(cmd.y)


def haversine_metres(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    lat1r = math.radians(lat1)
    lat2r = math.radians(lat2)
    a_val = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2.0) ** 2
    )
    return 6371000.0 * 2.0 * math.atan2(math.sqrt(a_val), math.sqrt(1.0 - a_val))


def set_param_confirm(vehicle, name, value, unit="", timeout_s=15):
    """Set a float param and wait until the vehicle reports it (best-effort)."""
    params = vehicle.parameters
    if name not in params:
        return False
    before = params.get(name)
    params[name] = float(value)
    suffix = " {}".format(unit) if unit else ""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        actual = params.get(name)
        if actual is not None and abs(actual - float(value)) < 0.25:
            print("  {}: {:.1f} -> {:.1f}{}".format(name, before, actual, suffix))
            return True
        time.sleep(0.5)
    actual = params.get(name)
    print(
        "WARN: {} is {:.1f} (wanted {:.1f}) — check in MAVProxy: param show {}".format(
            name, actual, value, name
        ),
        file=sys.stderr,
    )
    return False


def configure_rover_mission_params(vehicle):
    """Loosen acceptance and slow down for Gazebo skid-steer."""
    radius = vehicle.parameters.get("WP_RADIUS")
    if radius is not None and radius > 20.0:
        print(
            "WARN: WP_RADIUS={:.0f} m is huge — mission may advance while far from waypoints.".format(
                radius
            ),
            file=sys.stderr,
        )
        print("  Fix: ./scripts/start_sitl_gazebo.sh -w  or  param set WP_RADIUS 5", file=sys.stderr)
    set_param_confirm(vehicle, "WP_RADIUS", 5.0, unit="m")
    set_param_confirm(vehicle, "WP_SPEED", 1.0, unit="m/s")


def vehicle_position(vehicle):
    """Best-effort lat/lon for distance checks."""
    here = vehicle.location.global_relative_frame
    if here.lat is not None and abs(here.lat) > 1.0:
        return float(here.lat), float(here.lon)
    gps = vehicle.gps_0
    return float(gps.lat), float(gps.lon)


def max_mission_leg_metres(wps):
    longest = 0.0
    for i in range(1, len(wps)):
        a = command_lat_lon(wps[i - 1])
        b = command_lat_lon(wps[i])
        longest = max(longest, haversine_metres(a[0], a[1], b[0], b[1]))
    return longest


def leg_metres_to_waypoint(wps, seq):
    if seq <= 0 or seq >= len(wps):
        return 0.0
    a = command_lat_lon(wps[seq - 1])
    b = command_lat_lon(wps[seq])
    return haversine_metres(a[0], a[1], b[0], b[1])


def upload_mission(vehicle, wps, timeout_s=120):
    """Upload via DroneKit wploader (must not use raw recv_match — conflicts with DK thread)."""
    vehicle._wploader.clear()
    for wp in wps:
        vehicle._handler.fix_targets(wp)
        vehicle._wploader.add(wp)
    vehicle._wpts_dirty = True
    vehicle.commands.upload(timeout=timeout_s)


def mission_item_count(vehicle):
    """Raw mission size from pymavlink wploader (DroneKit commands.count is off by one)."""
    return vehicle._wploader.count()


def mission_item(vehicle, seq):
    """Mission item by sequence number (0-based, matches QGC file index)."""
    return vehicle._wploader.wp(seq)


def verify_mission_on_vehicle(vehicle, wps, timeout_s=30):
    """Download mission and compare lat/lon to catch upload corruption."""
    cmds = vehicle.commands
    cmds.download()
    if not cmds.wait_ready(timeout=timeout_s):
        print("WARN: mission download timed out", file=sys.stderr)
        return False

    on_board_count = mission_item_count(vehicle)
    if on_board_count < len(wps):
        print(
            "WARN: vehicle has {} mission items, file has {}".format(
                on_board_count, len(wps)
            ),
            file=sys.stderr,
        )
        return False

    for i, expected in enumerate(wps):
        on_board = mission_item(vehicle, i)
        if on_board is None:
            print("WARN: missing mission item {}".format(i), file=sys.stderr)
            return False
        lat_e, lon_e = command_lat_lon(expected)
        lat_o, lon_o = command_lat_lon(on_board)
        if abs(lat_o - lat_e) > 1e-5 or abs(lon_o - lon_e) > 1e-5:
            print(
                "ERROR: WP{} on vehicle ({:.7f}, {:.7f}) != file ({:.7f}, {:.7f})".format(
                    i, lat_o, lon_o, lat_e, lon_e
                ),
                file=sys.stderr,
            )
            return False
    print("Mission verified on vehicle ({} items).".format(len(wps)))
    return True


def distance_to_waypoint(vehicle, wps, seq):
    if seq < 0 or seq >= len(wps):
        return None
    target = mission_item(vehicle, seq)
    if target is None:
        target = wps[seq]
    tlat, tlon = command_lat_lon(target)
    rlat, rlon = vehicle_position(vehicle)
    return haversine_metres(rlat, rlon, tlat, tlon)


def format_position(lat, lon):
    return "{:.7f}, {:.7f}".format(lat, lon)


def wait_until_armable(vehicle, timeout_s=90):
    print("Waiting for vehicle to become armable...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if vehicle.is_armable:
            return True
        time.sleep(1)
    return False


def main():
    parser = argparse.ArgumentParser(description="Run AUTO mission from QGC waypoint file")
    parser.add_argument(
        "--connect",
        default="127.0.0.1:14550",
        help="MAVLink connection (default: 127.0.0.1:14550)",
    )
    parser.add_argument(
        "--mission",
        default="missions/my_street_loop.waypoints",
        help="Path to QGC .waypoints file",
    )
    parser.add_argument(
        "--home-tolerance",
        type=float,
        default=25.0,
        help="Max metres from WP0 before abort (default: 25)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Max seconds for mission (default: 600)",
    )
    parser.add_argument(
        "--max-leg-metres",
        type=float,
        default=None,
        help="Abort if closest approach to a WP exceeds this (default: auto from mission)",
    )
    parser.add_argument(
        "--no-stuck-abort",
        action="store_true",
        help="Do not abort when stuck far from a waypoint (debug only)",
    )
    args = parser.parse_args()

    wps = load_qgc_waypoints(args.mission)
    if len(wps) < 2:
        print("ERROR: need at least 2 waypoints", file=sys.stderr)
        sys.exit(1)

    print("Loaded {} waypoints from {}".format(len(wps), args.mission))
    for i, wp in enumerate(wps):
        lat, lon = command_lat_lon(wp)
        print("  WP{}: {:.7f}, {:.7f}  (accept radius param2={:.0f} m)".format(
            i, lat, lon, float(wp.param2)
        ))

    print("Connecting to {} ...".format(args.connect))
    vehicle = connect(args.connect, wait_ready=True, timeout=120)
    print("Connected. mode={} armed={}".format(vehicle.mode.name, vehicle.armed))
    gps = vehicle.gps_0
    print("GPS fix_type={} satellites={}".format(gps.fix_type, gps.satellites_visible))

    home = wps[0]
    home_lat, home_lon = command_lat_lon(home)
    here = vehicle.location.global_relative_frame
    dist_home = haversine_metres(here.lat, here.lon, home_lat, home_lon)
    print("Distance to mission WP0: {:.1f} m".format(dist_home))
    if dist_home > args.home_tolerance:
        print(
            "ERROR: Too far from mission home (>{:.0f} m). Align sim/location.env with WP0.".format(
                args.home_tolerance
            ),
            file=sys.stderr,
        )
        vehicle.close()
        sys.exit(1)

    configure_rover_mission_params(vehicle)

    print("Uploading mission...")
    upload_mission(vehicle, wps)
    print("Mission uploaded ({} items).".format(len(wps)))
    if not verify_mission_on_vehicle(vehicle, wps):
        vehicle.close()
        sys.exit(1)

    if not wait_until_armable(vehicle):
        print("ERROR: not armable", file=sys.stderr)
        vehicle.close()
        sys.exit(1)

    print("Switching to AUTO and arming...")
    vehicle.mode = VehicleMode("AUTO")
    vehicle.armed = True
    deadline = time.time() + 30
    while not vehicle.armed:
        if time.time() > deadline:
            print("ERROR: arm timeout", file=sys.stderr)
            vehicle.close()
            sys.exit(1)
        time.sleep(1)
    print("Armed in AUTO — mission running.")

    max_leg = max_mission_leg_metres(wps)
    stuck_limit = args.max_leg_metres
    if stuck_limit is None:
        stuck_limit = max(5.0 * max_leg, 50.0)
    print("Mission leg ~{:.0f} m; stuck-abort if closest approach > {:.0f} m".format(
        max_leg, stuck_limit
    ))

    start = time.time()
    last_seq = -1
    last_log = 0.0
    best_dist = {}
    seq_started = time.time()
    while time.time() - start < args.timeout:
        if vehicle.mode.name not in ("AUTO", "GUIDED"):
            print("Mode changed to {} — mission ended?".format(vehicle.mode.name))
            break
        seq = vehicle.commands.next
        dist = distance_to_waypoint(vehicle, wps, seq)
        if dist is not None:
            best_dist[seq] = min(best_dist.get(seq, dist), dist)
        if seq != last_seq:
            seq_started = time.time()
            rlat, rlon = vehicle_position(vehicle)
            tlat, tlon = command_lat_lon(wps[seq])
            leg = leg_metres_to_waypoint(wps, seq)
            if dist is not None:
                print(
                    "  active waypoint index: {}  (distance {:.1f} m, leg ~{:.0f} m)".format(
                        seq, dist, leg
                    )
                )
            else:
                print("  active waypoint index: {}".format(seq))
            print("    rover GPS:  {}".format(format_position(rlat, rlon)))
            print("    target WP{}: {}".format(seq, format_position(tlat, tlon)))
            if leg > 0 and dist is not None and dist > max(4.0 * leg, 40.0):
                print(
                    "WARN: Already far from WP{} on first fix — restart Gazebo+SITL (-w) "
                    "or check param show WP_RADIUS (want ~5 m).".format(seq),
                    file=sys.stderr,
                )
            last_seq = seq
        elif time.time() - last_log >= 10.0 and dist is not None:
            closest = best_dist.get(seq, dist)
            print(
                "  still on WP{} — distance {:.1f} m (closest so far {:.1f} m)".format(
                    seq, dist, closest
                )
            )
            last_log = time.time()
            on_wp = time.time() - seq_started
            if (
                not args.no_stuck_abort
                and on_wp >= 30.0
                and closest > stuck_limit
            ):
                rlat, rlon = vehicle_position(vehicle)
                tlat, tlon = command_lat_lon(wps[seq])
                print(
                    "ERROR: Stuck on WP{} for {:.0f}s (closest {:.0f} m, limit {:.0f} m).\n"
                    "  rover GPS:  {}\n"
                    "  target WP{}: {}\n"
                    "  Likely causes: WP_RADIUS too large (param show WP_RADIUS), "
                    "Gazebo not linked to SITL, or sim left running from an old session.\n"
                    "  Fix: ./scripts/stop_sim.sh then full restart; "
                    "start_sitl_gazebo.sh -w; retry. MAVProxy: mode HOLD".format(
                        seq,
                        on_wp,
                        closest,
                        stuck_limit,
                        format_position(rlat, rlon),
                        seq,
                        format_position(tlat, tlon),
                    ),
                    file=sys.stderr,
                )
                break
        if seq >= len(wps) - 1:
            here = vehicle.location.global_relative_frame
            end_lat, end_lon = command_lat_lon(wps[-1])
            if haversine_metres(here.lat, here.lon, end_lat, end_lon) < 8.0:
                print("Final waypoint reached.")
                break
        time.sleep(2)
    else:
        print("WARN: mission timeout", file=sys.stderr)

    print("Stopping (HOLD) and disarming...")
    vehicle.mode = VehicleMode("HOLD")
    time.sleep(2)
    vehicle.armed = False
    while vehicle.armed:
        time.sleep(1)
    print("Done.")
    vehicle.close()


if __name__ == "__main__":
    main()
