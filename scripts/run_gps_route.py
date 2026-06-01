#!/usr/bin/env python
"""
Drive rover from one GPS coordinate to another (DroneKit + ArduRover).

Typical flow:
  1) Start SITL with your desired home/start location.
  2) Run this script with --from-* and --to-* coordinates.
  3) Script arms in GUIDED, sends simple_goto(), waits until arrival,
     then switches HOLD and disarms.
"""

from __future__ import print_function

import argparse
import math
import sys
import time

from dronekit import LocationGlobalRelative, VehicleMode, connect


def haversine_metres(lat1, lon1, lat2, lon2):
    """Distance between two lat/lon points in metres."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    lat1r = math.radians(lat1)
    lat2r = math.radians(lat2)
    a_val = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2.0) ** 2
    )
    return 6371000.0 * 2.0 * math.atan2(math.sqrt(a_val), math.sqrt(1.0 - a_val))


def wait_until_armable(vehicle, timeout_s=60):
    deadline = time.time() + timeout_s
    print("Waiting for vehicle to become armable...")
    while time.time() < deadline:
        if vehicle.is_armable:
            return True
        time.sleep(1)
    return False


def arm_guided(vehicle, timeout_s=30):
    print("Switching to GUIDED and arming...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if vehicle.armed:
            return True
        time.sleep(1)
    return False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Drive ArduRover from one GPS coordinate to another"
    )
    parser.add_argument(
        "--connect",
        default="127.0.0.1:14550",
        help="MAVLink connection string (default: 127.0.0.1:14550)",
    )
    parser.add_argument("--from-lat", type=float, required=True, help="Start latitude")
    parser.add_argument("--from-lon", type=float, required=True, help="Start longitude")
    parser.add_argument("--to-lat", type=float, required=True, help="Destination latitude")
    parser.add_argument("--to-lon", type=float, required=True, help="Destination longitude")
    parser.add_argument(
        "--alt",
        type=float,
        default=0.0,
        help="Destination relative altitude (default: 0.0)",
    )
    parser.add_argument(
        "--start-tolerance",
        type=float,
        default=20.0,
        help="Max metres from --from-* before abort (default: 20m)",
    )
    parser.add_argument(
        "--arrival-tolerance",
        type=float,
        default=2.0,
        help="Target arrival radius in metres (default: 2m)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=240,
        help="Max seconds allowed to reach destination (default: 240)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("Connecting to {} ...".format(args.connect))
    vehicle = connect(args.connect, wait_ready=True, timeout=120)
    print("Connected. mode={} armed={}".format(vehicle.mode.name, vehicle.armed))

    current = vehicle.location.global_relative_frame
    dist_from_start = haversine_metres(
        current.lat, current.lon, args.from_lat, args.from_lon
    )
    print("Distance from declared start: {:.1f} m".format(dist_from_start))
    if dist_from_start > args.start_tolerance:
        print(
            "ERROR: Current rover position is too far from --from-* (>{:.1f} m).".format(
                args.start_tolerance
            ),
            file=sys.stderr,
        )
        print(
            "Tip: restart SITL with matching location or update --from-* coordinates.",
            file=sys.stderr,
        )
        vehicle.close()
        sys.exit(1)

    route_len = haversine_metres(args.from_lat, args.from_lon, args.to_lat, args.to_lon)
    print("Planned route length: {:.1f} m".format(route_len))

    if not wait_until_armable(vehicle):
        print("ERROR: Vehicle not armable in time", file=sys.stderr)
        vehicle.close()
        sys.exit(1)

    if not arm_guided(vehicle):
        print("ERROR: Failed to arm in GUIDED", file=sys.stderr)
        vehicle.close()
        sys.exit(1)
    print("Armed.")

    target = LocationGlobalRelative(args.to_lat, args.to_lon, args.alt)
    print(
        "Driving to destination: ({:.7f}, {:.7f})".format(args.to_lat, args.to_lon)
    )
    vehicle.simple_goto(target)

    deadline = time.time() + args.timeout
    reached = False
    while time.time() < deadline:
        here = vehicle.location.global_relative_frame
        remaining = haversine_metres(here.lat, here.lon, args.to_lat, args.to_lon)
        print("  remaining: {:.1f} m".format(remaining))
        if remaining <= args.arrival_tolerance:
            reached = True
            break
        time.sleep(2)

    if reached:
        print("Destination reached.")
    else:
        print("WARN: Timed out before reaching destination.", file=sys.stderr)

    print("Switching HOLD and disarming...")
    vehicle.mode = VehicleMode("HOLD")
    time.sleep(2)
    vehicle.armed = False
    while vehicle.armed:
        time.sleep(1)
    print("Done.")
    vehicle.close()


if __name__ == "__main__":
    main()
