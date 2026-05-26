#!/usr/bin/env bash
# Stop ArduRover SITL, MAVProxy, and related sim processes.

set -euo pipefail

echo "Stopping rover SITL / MAVProxy processes..."

patterns=(
  "sim_vehicle.py"
  "ardurover"
  "mavproxy.py"
  "MAVProxy"
)

for pat in "${patterns[@]}"; do
  pids=$(pgrep -f "${pat}" 2>/dev/null || true)
  if [[ -n "${pids}" ]]; then
    echo "  killing: ${pat}"
    echo "${pids}" | xargs kill -TERM 2>/dev/null || true
  fi
done

sleep 1

for pat in "${patterns[@]}"; do
  pids=$(pgrep -f "${pat}" 2>/dev/null || true)
  if [[ -n "${pids}" ]]; then
    echo "  force kill: ${pat}"
    echo "${pids}" | xargs kill -KILL 2>/dev/null || true
  fi
done

echo "Done."
