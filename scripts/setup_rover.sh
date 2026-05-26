#!/usr/bin/env bash
# Source this file from other scripts, or: source scripts/setup_rover.sh
#
# Sets project paths, activates Python 3.9 venv, and prepends ArduPilot tools.

if [[ -n "${ROVER_SETUP_DONE:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi

_ROVER_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
export ROVER_PROJECT_ROOT="$(cd "${_ROVER_SCRIPT_DIR}/.." && pwd)"
export ROVER_SETUP_DONE=1

# Python 3.9 venv (DroneKit-compatible)
if [[ -f "${ROVER_PROJECT_ROOT}/.venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "${ROVER_PROJECT_ROOT}/.venv/bin/activate"
else
  echo "WARN: .venv not found. Run: /opt/homebrew/bin/python3.9 -m venv .venv && pip install -r requirements.txt" >&2
fi

# ArduPilot SITL tools (sim_vehicle.py)
if [[ -d "${ROVER_PROJECT_ROOT}/ardupilot" ]]; then
  export PATH="${ROVER_PROJECT_ROOT}/ardupilot/Tools/autotest:${PATH}"
fi

# Module 2+: Gazebo Harmonic (macOS Homebrew typical paths)
if command -v gz >/dev/null 2>&1; then
  export GZ_VERSION="${GZ_VERSION:-harmonic}"
fi

export ROVER_PROJECT_ROOT
