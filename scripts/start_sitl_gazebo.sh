#!/usr/bin/env bash
# Terminal 3 (Module 2): ArduRover SITL + MAVProxy for Gazebo (JSON model).
#
# Prerequisites:
#   1) ./scripts/gazebo_server.sh   (wait for world + rover model)
#   2) ./scripts/gazebo_gui.sh      (optional, for 3D view)
#
# Usage: ./scripts/start_sitl_gazebo.sh [-w] [extra sim_vehicle.py args]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setup_rover.sh
source "${SCRIPT_DIR}/setup_rover.sh"
# shellcheck source=setup_gazebo.sh
source "${SCRIPT_DIR}/setup_gazebo.sh"

AP_DIR="${ROVER_PROJECT_ROOT}/ardupilot"
if [[ ! -d "${AP_DIR}" ]]; then
  echo "ERROR: ardupilot/ not found." >&2
  exit 1
fi
if [[ ! -f "${AP_DIR}/build/sitl/bin/ardurover" ]]; then
  echo "ERROR: ardurover not built." >&2
  exit 1
fi
if [[ ! -d "${ARDUPILOT_GAZEBO_DIR}/build" ]]; then
  echo "ERROR: ardupilot_gazebo not built at ${ARDUPILOT_GAZEBO_DIR}" >&2
  echo "  See docs/module-2-gazebo.md" >&2
  exit 1
fi

cd "${AP_DIR}"

LOC_ENV="${ROVER_PROJECT_ROOT}/sim/location.env"
CUSTOM_LOCATION=""
if [[ -f "${LOC_ENV}" ]]; then
  # shellcheck source=/dev/null
  source "${LOC_ENV}"
  if [[ -n "${ROVER_HOME_LAT:-}" && -n "${ROVER_HOME_LNG:-}" && -n "${ROVER_HOME_ALT:-}" && -n "${ROVER_HOME_HEADING:-}" ]]; then
    CUSTOM_LOCATION="${ROVER_HOME_LAT},${ROVER_HOME_LNG},${ROVER_HOME_ALT},${ROVER_HOME_HEADING}"
  fi
fi

SIM_EXTRA_ARGS=()
if [[ -n "${CUSTOM_LOCATION}" ]]; then
  SIM_EXTRA_ARGS+=(--custom-location "${CUSTOM_LOCATION}")
fi

echo "Starting ArduRover SITL for Gazebo (frame: gazebo-rover, model: JSON)"
echo "  Mission:  python scripts/run_mission.py"
echo "  Stop:     ./scripts/stop_sim.sh"
if [[ -n "${CUSTOM_LOCATION}" ]]; then
  echo "  Home:     ${CUSTOM_LOCATION}"
fi
echo ""

exec python Tools/autotest/sim_vehicle.py \
  -v Rover \
  -f gazebo-rover \
  --model JSON \
  --console \
  --map \
  "${SIM_EXTRA_ARGS[@]}" \
  "$@"
