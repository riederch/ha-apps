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
