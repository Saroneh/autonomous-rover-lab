#!/usr/bin/env python
"""
Module 1 — DroneKit hello for ArduRover SITL.

Connects to MAVProxy UDP output (default 127.0.0.1:14550), switches to GUIDED,
arms, drives ~5 m north via simple_goto, then disarms.

Prerequisites:
  Terminal 1: ./scripts/start_sitl.sh   (wait for heartbeat in MAVProxy)
  Terminal 2: python scripts/run_hello.py
"""

from __future__ import print_function

import argparse
import math
import sys
import time

from dronekit import connect, LocationGlobalRelative, VehicleMode


def get_distance_metres(a, b):
    """Haversine distance between two LocationGlobalRelative points (metres)."""
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lon - a.lon)
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    a_val = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    )
    return 6371000.0 * 2 * math.atan2(math.sqrt(a_val), math.sqrt(1 - a_val))


def wait_until_armable(vehicle, timeout=60):
    print("Waiting for vehicle to become armable...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if vehicle.is_armable:
            return True
        time.sleep(1)
    return False


def arm_and_wait(vehicle, timeout=30):
    print("Arming...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    deadline = time.time() + timeout
    while not vehicle.armed:
        if time.time() > deadline:
            return False
        print("  waiting for arm...")
        time.sleep(1)
    return True


def main():
    parser = argparse.ArgumentParser(description="ArduRover SITL DroneKit hello")
    parser.add_argument(
        "--connect",
        default="127.0.0.1:14550",
        help="MAVLink connection (MAVProxy --out, default UDP 14550)",
    )
    parser.add_argument(
        "--distance",
        type=float,
        default=5.0,
        help="Forward distance in metres (default 5)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1.0,
        help="Stop when within this many metres of target (default 1)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Max seconds to reach target (default 120)",
    )
    args = parser.parse_args()

    print("Connecting to {} ...".format(args.connect))
    vehicle = connect(args.connect, wait_ready=True, timeout=120)
    print("Connected. Mode={}, armed={}".format(vehicle.mode.name, vehicle.armed))

    if not wait_until_armable(vehicle):
        print("ERROR: Vehicle not armable (check SITL / EKF / prearm)", file=sys.stderr)
        vehicle.close()
        sys.exit(1)

    if not arm_and_wait(vehicle):
        print("ERROR: Failed to arm", file=sys.stderr)
        vehicle.close()
        sys.exit(1)
    print("Armed.")

    start = vehicle.location.global_relative_frame
    # ~111_111 m per degree latitude at equator; good enough for SITL hello
    target = LocationGlobalRelative(
        start.lat + (args.distance / 111111.0),
        start.lon,
        start.alt,
    )

    print(
        "Driving {:.1f} m north: ({:.7f},{:.7f}) -> ({:.7f},{:.7f})".format(
            args.distance,
            start.lat,
            start.lon,
            target.lat,
            target.lon,
        )
    )
    vehicle.simple_goto(target)

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        here = vehicle.location.global_relative_frame
        dist = get_distance_metres(here, target)
        print("  distance to target: {:.1f} m".format(dist))
        if dist <= args.tolerance:
            print("Target reached.")
            break
        time.sleep(2)
    else:
        print("WARN: Timeout before reaching target", file=sys.stderr)

    print("Stopping (HOLD) and disarming...")
    vehicle.mode = VehicleMode("HOLD")
    time.sleep(2)
    vehicle.armed = False
    while vehicle.armed:
        print("  waiting for disarm...")
        time.sleep(1)

    print("Done.")
    vehicle.close()


if __name__ == "__main__":
    main()
