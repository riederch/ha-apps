# A1 – Anlage-/Dateiinventar und Originalitätsprüfung

**Ziel:** Dateien, die beim Löschen eines Vorgängerchats verloren gehen könnten, erhalten bzw. ihre separate Library-Verfügbarkeit belegen. Eine Library-Datei mit passendem Zeitstempel ist nicht automatisch ein nachgewiesener Anhang des betreffenden Chats. Zeit-/Inhaltsnähe ist ein **Kandidatennachweis**, keine bestätigte Chat-Zuordnung.

| Datei und Quelle | Beobachtung | Beweisstatus | Erhalt |
|---|---|---|---|
| `originale/image(6).png` – Library-Datei, hochgeladen **02.11.2026 15:05 UTC** | Original-Screenshot des Home-Assistant-Dashboards mit zwei nebeneinander sichtbaren Energieflussdarstellungen, PV/Netz/Haus/Batterie. Wichtig für frühere visuelle Anforderungen. | Originaldatei nachweislich vorhanden und visuell geprüft; exakte Zuordnung zu S1 ohne vollständigen Chat nicht bestätigt. | Unveränderte Binärkopie in diesem Paket; SHA-256 im Manifest. |
| `originale/sofar_modbus_coordinator_patch_2026_10.zip` – Library-Datei, erzeugt **01.11.2026 12:33 UTC** | Recovery-Kandidat `sofar_link_recovery_2026.10.1.patch`, Tests, Installer und README. Inhalt sagt ausdrücklich **nicht an echter Hardware validiert**. | Original-Archiv geprüft (12 Dateien); eine direkte Chat-Metadatenzuordnung ist nicht belegt. | Unveränderte Binärkopie im Paket; SHA-256 im Manifest. |
| `home-assistant_sofar_2026-11-09T14-25-53.291Z.log` und `...56.298Z.log` | Library führt zwei vorhandene Original-Logs aus dem **separaten** Sofar-Patch-Faden. | Relevanz für Z1, nicht S1/S2 belegt. | Externe Library-Dateien vorhanden; **nicht** in dieses Local-EMS-Exportpaket kopiert. Z1 benötigt eigenes Inventar/Prüfung. |
| Sonstige Bilder/Anhänge aus S1/S2 | Noch nicht vollständig bekannt, u.a. alte Konfigurationen, Screenshots aus Zwischenständen und Fehlerlogs. | Ohne vollständiges Chattranskript keine Vollständigkeitsprüfung möglich. | **Offen**, Löschfreigabe gesperrt. |

## Original-Patch im Detail

Das Recovery-Paket ist ein von einem **Modbus-Write-Response-Fehler** getrenntes Thema: Es behandelt eine offene, aber nicht mehr antwortende TCP-Sitzung. Laut `README.md` soll der *Readings*-Coordinator bei drei vollständigen Aktualisierungs-Timeouts die Verbindung gezielt zurücksetzen, höchstens einmal alle 180 Sekunden; teilweise erfolgreiche Aktualisierungen setzen den Fehlerzähler zurück. Das Paket beinhaltet **keine automatische Behebung des Modbus-Register-4368-Schreibfehlers**, und eine Installation bzw. Hardwareabnahme wurde nicht nachgewiesen.

## Datenschutz und Grenzen

Originaldateien im Paket nicht als Nachweis eines produktiven Erfolgs interpretieren. Nicht projektbezogene Medien aus der Library wurden ausgeschlossen. Eine Sichtung weiterer Ursprungsdateien ist erforderlich, bevor ein gesamter Ursprungschat gelöscht werden kann.