#!/usr/bin/env bash
set -euo pipefail
profile="${1:-nabeel/obs/profile.ini.example}"
grep -q '^BaseCX=1920$' "$profile"
grep -q '^BaseCY=1080$' "$profile"
grep -q '^OutputCX=1920$' "$profile"
grep -q '^OutputCY=1080$' "$profile"
grep -q '^FPSCommon=60$' "$profile"
grep -q '^RecFormat=mkv$' "$profile"
echo "NABEEL_OBS_PROFILE=PASS"
echo "RUNTIME_30_MINUTE_RECORDING=PENDING"
