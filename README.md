# Home Assistant Apps

Eigenes Home-Assistant-App-Repository von Christoph Rieder.

## Enthaltene Apps

| App | Zweck |
|---|---|
| **Gitea** | Selbst gehosteter Git-Server direkt unter Home Assistant OS |
| **Gitea MCP** | Schlanker Wrapper um den offiziellen Gitea-MCP-Server mit optionalem Read-only-Modus |
| **Vaultwarden** | Selbst gehosteter, Bitwarden-kompatibler Passwortmanager |
| **Cloudflared Origin Auth** | Cloudflare Tunnel mit optionalem Basic-/Bearer-Zugriffsschutz für zusätzliche Hosts |

## Repository in Home Assistant hinzufügen

1. **Einstellungen → Apps → App-Store** öffnen.
2. Rechts oben **⋮ → Repositories** wählen.
3. Folgende URL hinzufügen:

   ```text
   https://github.com/riederch/ha-apps
   ```

4. Den App-Store aktualisieren.
5. Danach die gewünschten Apps aus diesem Repository installieren.

## Sicherheit

Für Gitea MCP wird ein Gitea-Zugriffstoken nicht dauerhaft in der App gespeichert. Im HTTP-Modus sendet der jeweilige MCP-Client den Token als Bearer-Token. Für reine Wissensabfragen kann die MCP-App zusätzlich mit `read_only: true` gestartet werden.

Vaultwarden generiert beim ersten Start einen temporären Admin-Token und zeigt ihn im App-Log an. Dieser sollte unmittelbar im Vaultwarden-Adminbereich gespeichert oder ersetzt werden.

Cloudflared Origin Auth verwendet für geschützte Zusatzhosts einen ausschließlich auf `127.0.0.1` gebundenen Nginx-Proxy im App-Container. Dieser prüft eingehende Basic- oder Bearer-Zugangsdaten, bevor der Request zum internen Origin-Dienst weitergeleitet wird. Die Zugangsdaten werden nicht an den Origin weitergereicht und nicht in die erzeugte Cloudflared-Ingress-Konfiguration geschrieben.

## Migrationen

Bestehende Installationen werden bei Versionswechseln nach Möglichkeit ohne manuelle Neukonfiguration übernommen. Versionsspezifische Hinweise, Rollback-Punkte und unveränderte Datenpfade sind in [`MIGRATIONS.md`](MIGRATIONS.md) dokumentiert.

## Aktuelle Runtime-Stände

- Gitea: `1.27.2`
- Gitea MCP: `1.7.0`
- Vaultwarden: `1.37.2`
- Cloudflared: `2026.8.3`

## Herkunft

Die Gitea-App verwendet die etablierte Gitea-App aus [`alexbelgium/hassio-addons`](https://github.com/alexbelgium/hassio-addons/tree/master/gitea) als Runtime-Image.

Gitea MCP verwendet den offiziellen Gitea-MCP-Server `1.7.0` aus `docker.gitea.com/gitea-mcp-server`; der lokale Code ist nur der Home-Assistant-Startwrapper.

Die Vaultwarden-App basiert auf [`hassio-addons/app-vaultwarden`](https://github.com/hassio-addons/app-vaultwarden) und verwendet Vaultwarden `1.37.2`.

Cloudflared Origin Auth ist ein schlanker Overlay-Fork von [`homeassistant-apps/app-cloudflared`](https://github.com/homeassistant-apps/app-cloudflared), aktuell auf App-Basis `7.0.14` mit Cloudflared `2026.8.3`. Details zu den übernommenen Komponenten stehen in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
