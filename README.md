# Home Assistant Apps

Eigenes Home-Assistant-App-Repository von Christoph Rieder.

## Enthaltene Apps

| App | Zweck |
|---|---|
| **Gitea** | Selbst gehosteter Git-Server direkt unter Home Assistant OS |
| **Gitea MCP** | Read-only-fähiger MCP-Zugang zu einer Gitea-Instanz, unter anderem für ChatGPT |

## Repository in Home Assistant hinzufügen

1. **Einstellungen → Apps → App-Store** öffnen.
2. Rechts oben **⋮ → Repositories** wählen.
3. Folgende URL hinzufügen:

   ```text
   https://github.com/riederch/ha-apps
   ```

4. Den App-Store aktualisieren.
5. Danach **Gitea** und **Gitea MCP** aus diesem Repository installieren.

## Sicherheit

Für Gitea MCP wird ein Gitea-Zugriffstoken nicht dauerhaft in der App gespeichert. Im HTTP-Modus sendet der jeweilige MCP-Client den Token als Bearer-Token. Für reine Wissensabfragen sollte in Gitea ein Token mit ausschließlich lesenden Rechten verwendet und die MCP-App im Read-only-Modus betrieben werden.

## Herkunft

Die Gitea-App orientiert sich an der Gitea-App aus [`alexbelgium/hassio-addons`](https://github.com/alexbelgium/hassio-addons/tree/master/gitea), wurde für dieses Repository jedoch eigenständig und reduziert umgesetzt. Details stehen in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
