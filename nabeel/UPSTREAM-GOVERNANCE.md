# NABEEL Station upstream governance

NABEEL Station keeps upstream open-source projects intact and layers Codestra/NABEEL integration on dedicated branches and `nabeel/` paths.

| Component | Codestra origin | Official upstream | Verified upstream HEAD |
| --- | --- | --- | --- |
| Chiaki | https://github.com/ingtrader21-spec/Chiaki.git | https://github.com/streetpea/chiaki-ng.git | a9a2805884cfa83865fdfcc09ca3ddfcd628aa42 |
| OBS Studio | https://github.com/ingtrader21-spec/OBS-Studio-Nabeel-.git | https://github.com/obsproject/obs-studio.git | e9f043d4ec47fb7da55086cc15bfd0a4fec53344 |
| MediaMTX | https://github.com/ingtrader21-spec/MediaMTX.git | https://github.com/bluenviron/mediamtx.git | ac377bcd0201d9dcad8326986d9cff452d357e4d |
| Owncast | https://github.com/ingtrader21-spec/Owncast-Nabeel.git | https://github.com/owncast/owncast.git | 21a6f5670ef4c0e13750e2987729ae57de7f7f8c |

## Branch policy

- `origin` is always the ingtrader21-spec repository.
- `upstream` is always the official open-source repository.
- NABEEL customizations live on dedicated integration/feature branches or under `nabeel/`.
- Never vendor or duplicate upstream source unnecessarily.
- Before rebasing NABEEL work, fetch upstream and preserve local integration commits.
- Pairing credentials, stream keys, admin passwords, tokens, and provider secrets never belong in Git.

The upstream HEADs above were read back successfully from the Ubuntu desktop on 2026-09-26.
