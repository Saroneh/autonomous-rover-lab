#!/usr/bin/env bash
# Terminal 1 (Module 2): Gazebo server — physics + world (no GUI).
#
# Usage: ./scripts/gazebo_server.sh [world.sdf]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setup_rover.sh
source "${SCRIPT_DIR}/setup_rover.sh"
# shellcheck source=setup_gazebo.sh
source "${SCRIPT_DIR}/setup_gazebo.sh"

WORLD="${1:-${GAZEBO_WORLD}}"

if [[ -f "${WORLD}" ]]; then
  WORLD_PATH="${WORLD}"
elif [[ -f "${ROVER_PROJECT_ROOT}/sim/worlds/${WORLD}" ]]; then
  WORLD_PATH="${ROVER_PROJECT_ROOT}/sim/worlds/${WORLD}"
else
  WORLD_PATH="${WORLD}"
fi

if ! command -v gz >/dev/null 2>&1; then
  echo "ERROR: gz not found. Install Gazebo Harmonic (brew install gz-harmonic)." >&2
  exit 1
fi

if [[ ! -d "${ARDUPILOT_GAZEBO_DIR}/build" ]]; then
  echo "WARN: ${ARDUPILOT_GAZEBO_DIR}/build not found — build ardupilot_gazebo first." >&2
  echo "  See docs/module-2-gazebo.md" >&2
fi

echo "Gazebo server: ${WORLD_PATH}"
echo "  GUI (other terminal): ./scripts/gazebo_gui.sh"
echo "  SITL (after world loads): ./scripts/start_sitl_gazebo.sh"
echo ""

exec gz sim -s -r "${WORLD_PATH}" -v 3
