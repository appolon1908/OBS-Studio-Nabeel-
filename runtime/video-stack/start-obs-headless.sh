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

def put_section(text: str, name: str, body: str) -> str:
    section=f"[{name}]\n{body.rstrip()}\n"
    pattern=re.compile(rf"(?ms)^\[{re.escape(name)}\]\n.*?(?=^\[|\Z)")
    if pattern.search(text):
        return pattern.sub(section+"\n",text)
    return (text.rstrip()+"\n\n"+section) if text.strip() else section

text=put_section(text,"OBSWebSocket",f"""FirstLoad=false
ServerEnabled=true
ServerPort=4455
AlertsEnabled=false
AuthRequired=true
ServerPassword={password}""")

basic_match=re.search(r"(?ms)^\[BasicWindow\]\n.*?(?=^\[|\Z)",text)
if basic_match:
    block=basic_match.group(0)
    if re.search(r"(?m)^PreviewEnabled=",block):
        block=re.sub(r"(?m)^PreviewEnabled=.*$","PreviewEnabled=false",block)
    else:
        block=block.rstrip()+"\nPreviewEnabled=false\n"
    if re.search(r"(?m)^PreviewProgramMode=",block):
        block=re.sub(r"(?m)^PreviewProgramMode=.*$","PreviewProgramMode=false",block)
    text=text[:basic_match.start()]+block+text[basic_match.end():]
else:
    text=put_section(text,"BasicWindow","PreviewEnabled=false\nPreviewProgramMode=false")

path.write_text(text,encoding="utf-8")
path.chmod(0o600)
PY
exec /usr/bin/xvfb-run -a -s "-screen 0 1280x720x24" \
  /usr/bin/obs \
  --disable-shutdown-check \
  --websocket_ipv4_only
