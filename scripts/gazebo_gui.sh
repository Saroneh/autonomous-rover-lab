#!/usr/bin/env bash
# Terminal 2 (Module 2): Gazebo GUI — attach to running server.
#
# Start gazebo_server.sh first, wait for world to load, then run this.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setup_rover.sh
source "${SCRIPT_DIR}/setup_rover.sh"
# shellcheck source=setup_gazebo.sh
source "${SCRIPT_DIR}/setup_gazebo.sh"

if ! command -v gz >/dev/null 2>&1; then
  echo "ERROR: gz not found." >&2
  exit 1
fi

echo "Gazebo GUI (attach to server)..."
exec gz sim -g -v 3
