# Owncast desktop authority

The OBS/NABEEL stack uses the existing Owncast runtime on `codestra-desktop`.
There is no authoritative Owncast process on the middleware server.

Control topology:

```
Codestra Video Controller 127.0.0.1:18100
  -> desktop API gateway 10.0.0.73:18181
  -> Owncast 127.0.0.1:18080
```

Webhook topology:

```
Owncast on codestra-desktop
  -> signed POST http://10.0.0.220:18110/webhooks/owncast
  -> source-IP + HMAC-SHA256 + replay-window validation
  -> local event journal / controller readback
```

OBS keeps `obs-websocket` as its native API. Owncast keeps its official
access-token Integration API. No `/api/admin/*` Owncast route is proxied by
the desktop gateway.

The Owncast media/RTMP route is independent of the control API and remains
disabled until the desktop's actual RTMP listener is re-read and certified.
Do not add a duplicate Owncast runtime or direct provider-effect bypass.
