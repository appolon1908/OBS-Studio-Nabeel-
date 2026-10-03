# Video stack OBS bridge

OBS keeps its native **obs-websocket 5.x** control plane. No duplicate HTTP wrapper is introduced.

- local port: `4455`
- authentication: required through `OBS_WEBSOCKET_PASSWORD`
- display: Xvfb
- network: loopback only through the systemd IP policy
- no `--startstreaming` flag is used; live streaming remains disabled

The Codestra Video Controller connects to obs-websocket directly.
