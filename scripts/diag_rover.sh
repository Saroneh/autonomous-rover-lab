#!/usr/bin/env bash
# Quick health check for Module 1 toolchain.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setup_rover.sh
source "${SCRIPT_DIR}/setup_rover.sh"

ok()  { echo "  OK   $*"; }
fail(){ echo "  FAIL $*"; ERR=1; }

ERR=0
echo "=== autonomous-rover-lab diagnostics ==="
echo "Project: ${ROVER_PROJECT_ROOT}"
echo ""

# Python 3.9
echo "--- Python ---"
if command -v python >/dev/null 2>&1; then
  ver=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
  if python -c 'import sys; exit(0 if sys.version_info[:2] == (3, 9) else 1)' 2>/dev/null; then
    ok "python ${ver}"
  else
    fail "python ${ver} (need 3.9.x for DroneKit)"
  fi
else
  fail "python not in PATH"
fi

if [[ -d "${ROVER_PROJECT_ROOT}/.venv" ]]; then
  ok ".venv exists"
else
  fail ".venv missing — run: python3.9 -m venv .venv"
fi

echo ""
echo "--- Python packages ---"
if python -c "import dronekit" 2>/dev/null; then
  ver=$(python -c "import dronekit; print(getattr(dronekit, '__version__', 'installed'))" 2>/dev/null || echo "installed")
  ok "dronekit ${ver}"
else
  fail "dronekit not installed"
fi
if command -v mavproxy.py >/dev/null 2>&1; then
  ver=$(pip show MAVProxy 2>/dev/null | awk -F': ' '/^Version:/{print $2}')
  ok "MAVProxy ${ver:-installed}"
else
  fail "mavproxy.py not in PATH (pip install mavproxy==1.8.74)"
fi

echo ""
echo "--- ArduPilot SITL ---"
AP="${ROVER_PROJECT_ROOT}/ardupilot"
if [[ -d "${AP}" ]]; then
  ok "ardupilot/ present"
  if [[ -f "${AP}/build/sitl/bin/ardurover" ]]; then
    ok "build/sitl/bin/ardurover"
  else
    fail "ardurover not built — cd ardupilot && ./waf configure --board sitl && ./waf rover"
  fi
  if [[ -f "${AP}/Tools/autotest/sim_vehicle.py" ]]; then
    ok "sim_vehicle.py"
  else
    fail "sim_vehicle.py missing"
  fi
else
  fail "ardupilot/ missing — git submodule update --init --recursive"
fi

echo ""
echo "--- Network (when SITL running) ---"
if lsof -iTCP:5760 -sTCP:LISTEN >/dev/null 2>&1; then
  ok "TCP 5760 listening (SITL)"
else
  echo "  --   TCP 5760 not listening (start ./scripts/start_sitl.sh)"
fi
if lsof -iUDP:14550 >/dev/null 2>&1; then
  ok "UDP 14550 in use (MAVProxy out — DroneKit target)"
else
  echo "  --   UDP 14550 not active (normal when SITL stopped)"
fi

echo ""
echo "--- Gazebo (Module 2) ---"
if command -v gz >/dev/null 2>&1; then
  ok "gz $(gz sim --version 2>/dev/null | head -1 || echo 'installed')"
else
  fail "gz not installed (brew install gz-harmonic)"
fi
GZ_ENV="${ROVER_PROJECT_ROOT}/sim/gazebo.env"
if [[ -f "${GZ_ENV}" ]]; then
  # shellcheck source=/dev/null
  source "${GZ_ENV}"
fi
if [[ -d "${ARDUPILOT_GAZEBO_DIR:-}/build" ]]; then
  ok "ardupilot_gazebo build"
else
  echo "  --   ardupilot_gazebo not built (${ARDUPILOT_GAZEBO_DIR:-~/ardupilot_gazebo})"
fi
if [[ -d "${SITL_MODELS_DIR:-}/Gazebo/worlds" ]]; then
  ok "SITL_Models worlds"
else
  echo "  --   SITL_Models not cloned (${SITL_MODELS_DIR:-~/SITL_Models})"
fi

echo ""
if [[ "${ERR}" -eq 0 ]]; then
  echo "All critical checks passed."
else
  echo "Some checks failed — fix above before running SITL."
  exit 1
fi
