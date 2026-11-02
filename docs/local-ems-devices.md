# Local EMS – Geräteverwaltung (0.2.0b1)

## Zweck

Einmalige Konfiguration aller schaltbaren Flexverbraucher und Wallboxen über
**Einstellungen → Geräte & Dienste → Local EMS → Konfigurieren**.

Die Geräteverwaltung ist Teil derselben Home-Assistant-Integration wie der
bestehende Peak Monitor. Die Daten werden als Optionen des HA Config Entry
gespeichert. Ein weiterer Verbrauchszähler oder eine zusätzliche Datenbank
wird **nicht** betrieben.

## Bedienung

Das Konfigurationsmenü bietet:

- **Peak Monitor:** vorhandene Leistungsgrenzen und Messwertalter ändern.
- **Energie-Messwerte:** Netzleistung (positiv Bezug, negativ Einspeisung),
  PV-Leistung, Hauslast, Batterie-Leistung (positiv Entladung), SoC zuordnen.
- **Schaltverbraucher hinzufügen:** Heizstab, Heizlüfter oder sonstige
  Verbraucher mit `switch.*`-Entität hinterlegen.
- **Schaltverbraucher bearbeiten/entfernen:** beliebig viele Geräte verwalten.
- **Wallbox hinzufügen:** Ladeleistungssensor, Ladefreigabeschalter,
  Ladestrom-Zahlentität und Fahrzeug-Verbindungsstatus optional zuordnen.
  Mindestens eine Wallbox-Entität muss hinterlegt werden.
- **Wallbox bearbeiten/entfernen:** mehrere unabhängige Wallboxen möglich.

### Pro Schaltverbraucher

| Parameter | Verwendung |
|---|---|
| Bezeichnung | Eindeutiger Anzeigename, z.B. Heizstab Pufferspeicher |
| Typ | Heizstab, Heizlüfter, anderer |
| Schalter | Bestehende HA `switch.*`-Entität |
| Nennleistung (W) | Planungswert; optional echter Leistungssensor |
| Priorität 1–100 | Niedriger = früher berücksichtigt |
| Mindest-Einschaltdauer | Späterer Schutz gegen schnelles Abschalten |
| Mindest-Ausschaltdauer | Späterer Schutz gegen häufige Starts |
| Überschussreserve (W) | Planungs-Sicherheitszuschlag |
| Berücksichtigen | Markiert Gerät für spätere Planung |

### Pro Wallbox

| Parameter | Verwendung |
|---|---|
| Bezeichnung | z.B. go-e |
| Ladeleistung | Bestehende HA `sensor.*`-Entität (optional) |
| Ladefreigabe | Bestehende HA `switch.*`-Entität (optional) |
| Ladestrom | Bestehende HA `number.*`-Entität (optional) |
| Fahrzeug verbunden | Bestehende HA `binary_sensor.*`-Entität (optional) |
| Phasen | 1 oder 3, zunächst reine Planung |
| Maximalstrom | 6–80 A, zunächst reine Planung |
| Priorität und Berücksichtigen | Zukunftsplanung |

Die Eingaben sind keine Herstellerkommandos; insbesondere dürfen
Ladefreigabe- und Stromlimit-Entitäten nicht ohne Prüfung der
zugrunde liegenden go-e-Integration für spätere Schreibaktionen benutzt werden.

## Sichtbare Statuswerte in HA

Es werden fünf zusätzliche native Sensoren angelegt: registrierte
Schaltverbraucher, aktuell eingeschaltete Schaltverbraucher, nicht
verfügbare Schaltverbraucher, *geschätzte* aktive Verbraucherleistung und
registrierte Wallboxen. Die beiden Anzahl-Sensoren enthalten die jeweilige
Konfiguration und beobachteten Zustände als Attribute.

Ist ein Leistungssensor hinterlegt, wird dessen Wert für den angezeigten
Schätzwert verwendet; andernfalls die hinterlegte Nennleistung.
Die Schätzung ist **kein abrechnungsrelevanter Messwert**.

## Betriebsgrenze: read-only

**Version 0.2.0b1 schaltet niemals einen Verbraucher und setzt keine
Wallbox-Ladeparameter.** Es werden ausschließlich bekannte HA-Entitäten
ausgelesen und Konfigurationswerte im HA Config Entry verändert.

Vor einer automatischen Überschussregelung sind zu definieren und zu testen:
Verhalten bei unzuverlässigen Daten, Einspeisung und Batterieentladung,
Mindestlaufzeiten, Prioritäten, elektrische Schaltlasten der Relais und
manuelle Bedienung beziehungsweise Sicherheitsabschaltung. Für manche
Heizlüfter oder Heizstäbe muss geprüft werden, ob das externe Schalten über
ein Relais betrieblich und elektrisch zulässig ist.

## Upgrade von 0.1.x

In HACS `Local EMS` aktualisieren und HA neu starten. Die vorhandene
Peak-Monitor-Config-Entry und deren Einstellungen bleiben bestehen. Im
Integrationseintrag unter **Konfigurieren** erscheint ein neues Menü.
Für registrierte Verbraucher sind keine YAML-Einträge erforderlich.

Regulärer Status: `Beta`. HACS/Hassfest und Unit-Tests sichern die
Struktur, aber nicht das reale Schaltverhalten (da nicht implementiert).
