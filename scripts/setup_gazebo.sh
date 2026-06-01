#!/usr/bin/env bash
# Source after setup_rover.sh — sets Gazebo plugin/model paths for ArduPilot SITL.
#
# Usage: source scripts/setup_rover.sh && source scripts/setup_gazebo.sh

_ROVER_GZ_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_ROVER_GZ_ROOT="$(cd "${_ROVER_GZ_SCRIPT_DIR}/.." && pwd)"

if [[ -z "${ROVER_PROJECT_ROOT:-}" ]]; then
  # shellcheck source=setup_rover.sh
  source "${_ROVER_GZ_SCRIPT_DIR}/setup_rover.sh"
fi

GZ_ENV="${ROVER_PROJECT_ROOT}/sim/gazebo.env"
if [[ -f "${GZ_ENV}" ]]; then
  # shellcheck source=/dev/null
  source "${GZ_ENV}"
fi

export GZ_VERSION="${GZ_VERSION:-harmonic}"

if [[ -d "${ARDUPILOT_GAZEBO_DIR}/build" ]]; then
  export GZ_SIM_SYSTEM_PLUGIN_PATH="${ARDUPILOT_GAZEBO_DIR}/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"
fi
if [[ -d "${ARDUPILOT_GAZEBO_DIR}/models" ]]; then
  export GZ_SIM_RESOURCE_PATH="${ARDUPILOT_GAZEBO_DIR}/models:${ARDUPILOT_GAZEBO_DIR}/worlds:${GZ_SIM_RESOURCE_PATH:-}"
fi
if [[ -d "${SITL_MODELS_DIR}/Gazebo" ]]; then
  export GZ_SIM_RESOURCE_PATH="${SITL_MODELS_DIR}/Gazebo/models:${SITL_MODELS_DIR}/Gazebo/worlds:${GZ_SIM_RESOURCE_PATH:-}"
fi
export GZ_SIM_RESOURCE_PATH="${ROVER_PROJECT_ROOT}/sim/worlds:${GZ_SIM_RESOURCE_PATH:-}"

export GAZEBO_WORLD="${GAZEBO_WORLD:-r1_rover_runway.sdf}"
