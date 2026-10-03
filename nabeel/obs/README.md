# NABEEL Station — OBS creator profile

The NABEEL profile targets 1080p60 gameplay recording with MKV as the fail-safe recording container. Remux/export happens after recording, never by recording directly to MP4.

Source bootstrap is in `nabeel/obs/profile.ini.example`. Copy it into a dedicated local OBS profile; do not overwrite a user's default profile.

Required runtime acceptance remains a real 30-minute recording:
- 1920x1080 @ 60 FPS;
- MKV output;
- gameplay audio + microphone;
- optional webcam/overlays;
- zero material dropped-frame or audio-sync defects;
- output stored in the documented local NABEEL recording directory.
