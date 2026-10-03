# Owncast desktop authority

The NABEEL/OBS stack uses the existing Owncast runtime on `codestra-desktop`.
There is no authoritative Owncast process on the middleware server.

Control topology:

```
Codestra Video Controller 127.0.0.1:18100
  -> Owncast server connector 127.0.0.1:18104
  -> desktop API bridge 10.0.0.73:18180
  -> Owncast 127.0.0.1:18080
```

Webhook topology:

```
Owncast on codestra-desktop
  -> signed POST http://10.0.0.220:18184/v1/webhooks/owncast
  -> signature + replay validation
  -> local event journal / Middleware ingestion boundary
```

OBS keeps `obs-websocket` as its native API. Owncast keeps its official
access-token Web API. Do not add direct provider-effect bypasses or a duplicate
Owncast runtime.
