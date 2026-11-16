# A1 - Stufe 1: aeltester belegbarer Local-EMS-Implementierungsabschnitt

**Status:** chronologischer Teilstand; nicht selbst die fuehrende Gespraechskarte.  
**Quellenklasse:** `R` = selektiver, nicht vollstaendig einsehbarer Gespraechskontext; `G` = unabhaengig erneut gepruefte GitHub-Historie.  
**Zeitstellung:** Der Chat **„SG Ready erklaert“** begann nach verfuegbarem Gespraechskontext am 01.11.2026. Der erste hier belastbar rekonstruierbare Local-EMS-Inhalt liegt am **02.11.2026**. Keine vollstaendige Ursprungstranskript-Datei ist vorhanden.

## Ausgangsproblem und Primärziel - 02.11.2026

- Eine bevorstehende **15-Minuten-Netzbezugs-Leistungsspitze** soll erkennbar und eine Warnung rechtzeitig ausgebbar sein; Startwert **10 kW Grenzwert**, **9 kW Vorwarnung** als Projektkonfiguration. [R/G]
- Local EMS soll spaeter PV, Wallbox, Batterie und Verbraucher koordinieren koennen, aber **zunaechst nur einen lesenden Peak-Monitor** bereitstellen. [R/G]
- Herstellerneutral: Sofar ist ein moeglicher Datengeber und darf keine architektonische Pflicht sein. [R]
- Vorhandene Home-Assistant-Sensorik, Recorder und Statistics nutzen, **keine zweite Verbrauchsdatenbank und keinen direkten SQL-Zugriff**. [R/G]
- Fuer abrechnungsnahen Viertelstundenbezug einen monotonen Bezug-Energiezaehler verwenden; Datenluecken, DST und Zaehlerspruenge sichtbar machen; der Prognosewert ist keine Messung. [G]

## Entscheidungsgeschichte und Gegenargumente

| Entscheidung | Erhaltene Gruende | Alternative/Nachteil | Beleglage |
| --- | --- | --- | --- |
| Native HA-Custom-Integration | Vorhandene Entitaeten, Recorder, Konfiguration und spaeter modulare Erweiterung | Separates Archiv/SQL fuehrt zu Doppelhaltung; HA-Datenluecken bleiben Restrisiko | R+G; Originaltranskript fehlt |
| Erste Phase rein lesend | Keine verfruehte, netz-/EPS-kritische Steuerung; Warnung genuegt als erste Funktion | Aktives Peak-Shaving/Wallbox/Batteriebefehle werden bewusst spaeter behandelt | R+G |
| Feste Viertelstunden | Netzbezugs-Peak zeitlich korrekt in 00/15/30/45-Fenstern betrachten | Datenqualitaet, unvollstaendige Fenster, Echtzeit- vs. amtliche Daten unterscheiden | G |
| Sofar nicht zwingend | Produkt- und herstellerneutrales EMS | Sofar-spezifische Statuswerte bleiben optionale Anbindung | R |

## Unabhaengig gepruefte Git-Historie des fruehen Abschnitts

- `a5398f2e70` vom 02.11.2026, 11:47 UTC: HA-native Viertelstunden-Peak-Monitor-Integration.
- `7cb8ca657b` vom 02.11.2026, 12:14 UTC: Anzeige unter Integrationen statt unter Helfern.
- `699f71df7b` vom 02.11.2026, 13:14 UTC: herstellerneutrale EPS-/Heartbeat-/Inverter-Statusanbindung.
- `46679d06c8` vom 02.11.2026, 14:22 UTC: integrierte Energy-Flow-Dashboard-Karte.
- `3e3447c852` vom 02.11.2026, 14:49 UTC: Power Flow Card Plus-Stil, Energy-Dashboard-Daten.
- `37bc34eea2` und `7f6e16eedc` vom 02.11.2026: Vollbreite bzw. fixe Bubbles.
- `54a9734829` vom 02.11.2026, 18:01 UTC: 15-Minuten-Ist-Durchschnitt und Gauge.

**Pruefgrenze:** Ein Git-Commit beweist den damaligen Codeaenderungsstand, nicht den gesamten Gespraechsinhalt oder die vollstaendige Abwaegung. Der ueberpruefte Git-Stand darf daher nicht als vollstaendiger Chat-Import bezeichnet werden.

## Stufe 1: Verarbeitungsstand

- Erfasste Anteile: Ausgangsproblem, technischer Pfad, zentrale Anforderungen und dokumentierte Gegenkriterien.
- Offen: vollstaendiger Originaltext, weitere dort verworfene Alternativen, gegebene Zustimmung zu jeder Einzelentscheidung, ggf. weitere Folgethemen.
- A1-Quellenstatus: **teilweise erreichbar / mit dokumentierter Luecke**.
- Loeschbereitschaft: **gesperrt** (A6-Quellenpruefung und unabhaengiger Wiederaufnahmetest fehlen).
- Naechste Stufe: Entscheidungen vom 08.11. (Direktfluesse und originale PFCP-Darstellung) ohne Rueckwirkung auf den fruehen Ursprung integrieren.

**Nachtrag zur Quellenabgrenzung (15.11.2026):** Frühere konzeptionelle Vorläufer von 2025 und Juli 2026 sind nun selektiv dokumentiert (`a1-wiedergefundene-fragmente.md`), aber keine automatisch identischen A1-Fortsetzungschats. S1 begann bereits am 01.11. mit Netzbetreiber-/SG-Ready-Fragen; die erste nachweisbare konkrete Local-EMS-Implementierungsstufe bleibt der 02.11.