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
- Runtime version: `1.6.0`
- Image source: `docker.gitea.com/gitea-mcp-server:1.6.0`
- Upstream license: MIT

The Home Assistant app does not maintain a source fork of Gitea MCP. It copies the official `gitea-mcp` binary into a small Alpine wrapper image and adds only Home Assistant configuration/startup handling.

## Vaultwarden Home Assistant App

The `vaultwarden` app is derived from Home Assistant Community Apps:

- Project: `hassio-addons/app-vaultwarden`
- Current Vaultwarden runtime: `vaultwarden/server:1.37.1`
- Home Assistant Debian base: `ghcr.io/hassio-addons/debian-base:9.4.0`
- Locally published image: `ghcr.io/riederch/ha-apps-vaultwarden`
- Upstream Home Assistant app integration license: MIT
- Copyright: 2019-2026 Franck Nijhof

The local copy is independently maintained in `riederch/ha-apps`. It retains the upstream Home Assistant integration structure while updating the Vaultwarden runtime and publishing its own multi-architecture image.

### MIT License notice

Copyright (c) 2019-2026 Franck Nijhof

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE.

## Cloudflared Origin Auth

The `cloudflared_auth` app is a small overlay derived from the Unofficial Home Assistant Apps Cloudflared integration:

- Project: `homeassistant-apps/app-cloudflared`
- Released Home Assistant app base: `7.0.13`
- Cloudflared runtime: `cloudflare/cloudflared` `2026.8.2`
- Base image: `ghcr.io/homeassistant-apps/cloudflared/{arch}:7.0.13`
- Upstream Home Assistant app integration license: MIT
- Copyright: 2026 Unofficial Home Assistant Apps

The local overlay keeps the latest released Home Assistant Cloudflared integration as its compatibility base, updates the Cloudflared binary to `2026.8.2`, and adds a loopback-only Nginx proxy that enforces optional per-host Basic or Bearer access protection before forwarding requests to internal origin services.

### MIT License notice

Copyright (c) 2026 Unofficial Home Assistant Apps

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE.
