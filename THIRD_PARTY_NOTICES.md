# Third-party notices

## Gitea Home Assistant App

The `gitea` app definition uses the prebuilt image maintained by AlexBelgium:

- Project: `alexbelgium/hassio-addons`
- App: `gitea`
- Runtime version: `1.27.2`
- Image: `ghcr.io/alexbelgium/gitea-{arch}`
- Upstream license: MIT

The local app definition intentionally retains the upstream image so that Home Assistant users only need to add `riederch/ha-apps` as their repository while still receiving the established Gitea runtime integration.

## Gitea MCP

The `gitea_mcp` app wraps the official Gitea MCP server:

- Project: `gitea.com/gitea/gitea-mcp`
- Runtime version: `1.8.0`
- Image source: `docker.gitea.com/gitea-mcp-server:1.8.0`
- Upstream license: MIT

The Home Assistant app does not maintain a source fork of Gitea MCP. It copies the official `gitea-mcp` binary into a small Alpine wrapper image and adds only Home Assistant configuration/startup handling. Existing app options and the `/mcp` endpoint are retained across the 1.6.0 to 1.8.0 migration.

## Gitea Runner

The `gitea_runner` app wraps the official Gitea Runner:

- Project: `gitea.com/gitea/runner`
- Runtime version: `5.0.0`
- Image source: `docker.io/gitea/runner:5.0.0`
- Upstream license: MIT

The Home Assistant app does not maintain a source fork of Gitea Runner. It uses the official runner image and adds only Home Assistant configuration, persistent registration handling, and a deliberately unprivileged host-mode execution profile.

## Vaultwarden Home Assistant App

The `vaultwarden` app is derived from Home Assistant Community Apps:

- Project: `hassio-addons/app-vaultwarden`
- Current Vaultwarden runtime: `vaultwarden/server:1.37.4`
- Home Assistant Debian base: `ghcr.io/hassio-addons/debian-base:9.5.0`
- Locally published image: `ghcr.io/riederch/ha-apps-vaultwarden`
- Upstream Home Assistant app integration license: MIT
- Copyright: 2019-2026 Franck Nijhof

The local copy is independently maintained in `riederch/ha-apps`. It retains the upstream Home Assistant integration structure while updating the Vaultwarden runtime and publishing its own multi-architecture image. Before the first local SQLite start on Vaultwarden 1.37.4 the wrapper creates a one-time pre-migration database backup.

### MIT License notice

Copyright (c) 2019-2026 Franck Nijhof

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Cloudflared Origin Auth

The `cloudflared_auth` app is a small overlay derived from the Unofficial Home Assistant Apps Cloudflared integration:

- Project: `homeassistant-apps/app-cloudflared`
- Released Home Assistant app base: `7.0.21`
- Cloudflared runtime: `cloudflare/cloudflared` `2026.10.7`
- Base image: `ghcr.io/homeassistant-apps/cloudflared/{arch}:7.0.21`
- Upstream Home Assistant app integration license: MIT
- Copyright: 2026 Unofficial Home Assistant Apps

The local overlay keeps the released Home Assistant Cloudflared integration as its compatibility base, uses the upstream-patched Cloudflared binary `2026.10.7`, and adds a loopback-only Nginx proxy that enforces optional per-host Basic or Bearer access protection before forwarding requests to internal origin services. Existing tunnel credentials and app options remain compatible with the 7.0.21 base migration.

### MIT License notice

Copyright (c) 2026 Unofficial Home Assistant Apps

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Power Flow Card Plus – embedded Local EMS Flow Card

- Original project: https://github.com/flixlix/power-flow-card-plus
- Upstream source monorepo: https://github.com/flixlix/flixlix-cards
- Distribution: **0.4.0-beta.1**, current published repository-main build
  as of 2026-11-08 (not the older 0.3.7 stable release).
- Exact pinned distribution commit:
  `d9f3a9255776b3e1a270bf72b2c8039e22047104`
- License: **MIT**
- Copyright: **Copyright (c) 2023-2026 flixlix**
- Bundled distribution: `custom_components/local_ems/frontend/vendor/power-flow-card-plus-v0.4.0-beta.1.mjs`
- Upstream MIT license: `custom_components/local_ems/frontend/vendor/LICENSE-PFCP`

**Modifications:** The current original JavaScript distribution was
vendored unchanged except for the six element/tag/selector literals
used for `power-flow-card-plus` and `power-flow-card-plus-editor`,
which were namespaced to `local-ems-pfcp-upstream` and
`local-ems-pfcp-upstream-editor` to avoid collisions with a
separately installed copy. Power-flow calculations, animation
timing, rendering, and layout logic remain directly from upstream.

The Local EMS GPL-licensed frontend wrapper and data adapter bridge the
existing HA Energy Dashboard/EMS sources to this original card.
They are not a reimplementation of Power Flow Card Plus.

The bundled compiled distribution incorporates upstream runtime
dependencies; review third-party dependency notices and licenses when
updating the upstream version.

### Original MIT license notice (Power Flow Card Plus)

```text
MIT License

Copyright (c) 2023-2026 flixlix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
