#!/usr/bin/env bash
set -euo pipefail
: "${OBS_WEBSOCKET_PASSWORD:?OBS_WEBSOCKET_PASSWORD must be set}"
export HOME="${OBS_HOME:-/var/lib/codestra-obs}"
CONFIG="$HOME/.config/obs-studio/global.ini"
mkdir -p "$(dirname "$CONFIG")"
python3 - "$CONFIG" "$OBS_WEBSOCKET_PASSWORD" <<'PY'
from pathlib import Path
import re, sys
path=Path(sys.argv[1])
password=sys.argv[2]
text=path.read_text(encoding="utf-8") if path.exists() else ""
section=(
    "[OBSWebSocket]\n"
    "FirstLoad=false\n"
    "ServerEnabled=true\n"
    "ServerPort=4455\n"
    "AlertsEnabled=false\n"
    "AuthRequired=true\n"
    f"ServerPassword={password}\n"
)
pattern=re.compile(r"(?ms)^\[OBSWebSocket\]\n.*?(?=^\[|\Z)")
if pattern.search(text):
    text=pattern.sub(section+"\n",text)
else:
    text=(text.rstrip()+"\n\n"+section) if text.strip() else section
path.write_text(text,encoding="utf-8")
path.chmod(0o600)
PY
exec /usr/bin/xvfb-run -a -s "-screen 0 1920x1080x24" \
  /usr/bin/obs \
  --disable-shutdown-check \
  --websocket_ipv4_only
