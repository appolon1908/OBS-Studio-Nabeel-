#!/usr/bin/env bash
set -euo pipefail
: "${OBS_WEBSOCKET_PASSWORD:?OBS_WEBSOCKET_PASSWORD must be set}"
export HOME="${OBS_HOME:-/var/lib/codestra-obs}"
mkdir -p "$HOME/.config/obs-studio"
exec /usr/bin/xvfb-run -a -s "-screen 0 1920x1080x24" \
  /usr/bin/obs \
  --disable-shutdown-check \
  --websocket_port 4455 \
  --websocket_password "$OBS_WEBSOCKET_PASSWORD" \
  --websocket_ipv4_only
