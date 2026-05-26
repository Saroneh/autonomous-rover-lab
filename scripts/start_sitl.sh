#!/usr/bin/env bash
# Start ArduRover SITL with MAVProxy (--console --map).
# MAVProxy must stay connected to TCP 5760 or SITL blocks waiting for a GCS.
#
# Usage: ./scripts/start_sitl.sh [extra sim_vehicle.py args]
#
# Terminal 2 (after heartbeat): python scripts/run_hello.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setup_rover.sh
source "${SCRIPT_DIR}/setup_rover.sh"

AP_DIR="${ROVER_PROJECT_ROOT}/ardupilot"
if [[ ! -d "${AP_DIR}" ]]; then
  echo "ERROR: ardupilot/ not found." >&2
  echo "  git submodule update --init --recursive" >&2
  echo "  cd ardupilot && ./waf configure --board sitl && ./waf rover" >&2
  exit 1
fi

if [[ ! -f "${AP_DIR}/build/sitl/bin/ardurover" ]]; then
  echo "ERROR: SITL binary not built. Run:" >&2
  echo "  cd ardupilot && ./waf configure --board sitl && ./waf rover" >&2
  exit 1
fi

cd "${AP_DIR}"
echo "Starting ArduRover SITL (frame: rover) — MAVProxy on UDP 14550"
echo "  DroneKit: python scripts/run_hello.py"
echo "  Stop:     ./scripts/stop_sim.sh"
echo ""

exec python Tools/autotest/sim_vehicle.py \
  -v Rover \
  -f rover \
  --console \
  --map \
  "$@"
