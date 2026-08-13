# Third-party notices

## Gitea Home Assistant App

The `gitea` app definition uses the prebuilt image maintained by AlexBelgium:

- Project: `alexbelgium/hassio-addons`
- App: `gitea`
- Image: `ghcr.io/alexbelgium/gitea-{arch}`
- Upstream license: MIT

The local app definition intentionally retains the upstream image so that Home Assistant users only need to add `riederch/ha-apps` as their repository while still receiving the established Gitea runtime integration.

## Gitea MCP

The `gitea_mcp` app packages the official Gitea MCP server image:

- Project: `gitea/gitea-mcp`
- Image: `docker.gitea.com/gitea-mcp-server`
- Upstream license: MIT

The surrounding Home Assistant startup wrapper is maintained in this repository.

## Vaultwarden Home Assistant App

The `vaultwarden` app is derived from Home Assistant Community Apps:

- Project: `hassio-addons/app-vaultwarden`
- Imported release: `v0.27.0`
- Vaultwarden image used by that release: `vaultwarden/server:1.36.0`
- Upstream Home Assistant app integration license: MIT
- Copyright: 2019-2026 Franck Nijhof

The local copy changes the Home Assistant app version from the upstream development placeholder (`dev`) to `0.27.0` and points the app metadata at `riederch/ha-apps`; the runtime behavior remains based on the upstream release.

### MIT License notice

Copyright (c) 2019-2026 Franck Nijhof

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
