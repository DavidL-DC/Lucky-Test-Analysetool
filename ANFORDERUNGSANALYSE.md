# Anforderungsanalyse, MVP-Stand und Roadmap

## 1. Zielbild

Das Lucky Test Analysetool ist eine lokale Windows-Desktop-Anwendung. Beim Start ruft sie über offizielle Schnittstellen die neuesten verfügbaren Kennzahlen der iOS-App und der zugehörigen TikTok-, Instagram- und YouTube-Kanäle ab. Nach der einmaligen Kontoeinrichtung sieht der Nutzer das Dashboard ohne manuelle Datenpflege.

## 2. Nutzer und Kernfragen

Primärer Nutzer ist der Betreiber von Lucky Test. Das Dashboard soll beantworten:

- Wie entwickeln sich Downloads und Bewertungen der App?
- Wie entwickeln sich Reichweite und Interaktionen je Social-Media-Kanal?
- Welche Beiträge erzielen besonders gute Ergebnisse?
- Wie aktuell sind die Daten und bei welcher Quelle fehlt ein neuer Import?

## 3. Rahmenbedingungen und Abgrenzung

- Betrieb lokal unter Windows, wahlweise aus VS Code oder als erzeugter One-folder-Build.
- Möglichst keine laufenden Kosten.
- YouTube und TikTok werden über die jeweils eingerichteten Konten angebunden;
  Instagram ist für offizielle Insights als Business-Konto konfiguriert.
- Ausschließlich offizielle APIs und OAuth-Verfahren; kein Scraping und keine inoffizielle Login-Automation.
- Konten, API-Apps, Berechtigungen und Tokens müssen einmalig eingerichtet werden.
- Instagram muss für Insights als Creator- oder Business-Konto geführt werden; ein normales Privatkonto reicht nicht.
- Keine Cloud-, Mehrbenutzer-, Posting-, Benachrichtigungs- oder KI-Funktionen im MVP.

## 4. Automatische Datenstrategie

| Quelle | Offizieller Datenweg | Voraussetzungen | Automatisierbare MVP-Daten | Einschätzung |
| --- | --- | --- | --- | --- |
| App Store | App Store Connect API / Analytics Reports API | aktives Developer-Konto, API-Schlüssel, geeignete Rolle | Downloads, Installationen, Updates, Reviews; weitere Analytics je Verfügbarkeit | gut machbar, Berichte können zeitversetzt sein |
| YouTube | YouTube Data API und YouTube Analytics API | Google-Cloud-Projekt, OAuth-Zustimmung des Kanalinhabers | Kanal-, Video-, View-, Like-, Kommentar-, Share- und Watchtime-Werte | gut machbar innerhalb des Kontingents |
| TikTok | TikTok Display API | Developer-Konto, registrierte und freigegebene App, Login Kit, OAuth-Scopes | eigene Videos, Views, Likes, Kommentare und Shares | machbar, aber Freigabe und Tokenpflege sind Hürden |
| Instagram | Instagram API mit Instagram Login | Creator-/Business-Konto, Meta-App, OAuth und Insights-Berechtigung | Konto- und Medien-Insights wie Reichweite, Aufrufe und Interaktionen | mit Privatkonto nicht machbar; Kontoumstellung erforderlich |

Der Abruf startet automatisch beim Öffnen der Anwendung und kann zusätzlich über „Jetzt aktualisieren“ ausgelöst werden. Jede Antwort wird mit Abrufzeitpunkt als Snapshot in SQLite gespeichert. So bleiben Zeitverläufe erhalten, auch wenn eine API nur aktuelle Zähler liefert.

„Aktuell“ bedeutet der neueste von der Plattform bereitgestellte Stand. Einige Plattformberichte werden verzögert verarbeitet; das Dashboard zeigt deshalb je Quelle `aktualisiert am`, `Datenstand` und den Zustand `aktuell`, `verzögert` oder `Fehler`.

## 5. Funktionaler MVP-Stand

### Umgesetzt

1. Lokale Konfiguration von App-IDs und OAuth-Verbindungen über `.local.env`.
2. Tokens und Schlüssel ausschließlich lokal einlesen und niemals in Git speichern.
3. Beim Start alle konfigurierten Quellen in einem Hintergrundthread aktualisieren, ohne die Oberfläche zu blockieren.
4. API-Antworten prüfen, normalisieren und als zeitgestempelte Snapshots in SQLite speichern.
5. Letzten erfolgreichen Abruf, Datenstand und Fehler pro Quelle anzeigen.
6. Bei einem Abruffehler die letzten gültigen Werte weiterverwenden.
7. Dashboard mit Start-, App-Store-, YouTube-, TikTok- und Instagram-Seite sowie zentraler Zeitraumwahl anzeigen.
8. Manuelle Aktualisierung, vollständige Beitragslisten und schriftliche App-Store-Rezensionen bereitstellen.
9. Reproduzierbaren lokalen Windows-One-folder-Build erzeugen.

### Nach dem MVP

- Zeitvergleiche zum vorherigen Zeitraum
- Filter nach Plattform und Beitrag
- geplante Hintergrundaktualisierung in einem wählbaren Intervall
- CSV-Export und lokale Datenbanksicherung
- weitere Designoptimierungen und gegebenenfalls Wechsel von CustomTkinter zu
  einem moderneren GUI-Toolkit
- private iOS-Anwendung ohne öffentliche App-Store-Veröffentlichung

## 6. Kennzahlen und Regeln

- **Interaktionen:** Likes + Kommentare + Shares, soweit die Quelle diese Werte liefert.
- **Interaktionsrate:** Interaktionen / Aufrufe × 100; bei 0 Aufrufen wird kein Wert angezeigt.
- **Aktueller Wert:** jüngster vorhandener Stichtag je Quelle beziehungsweise Beitrag.
- **Zeitraumänderung:** letzter minus erster Wert im gewählten Zeitraum; kumulative und stichtagsbezogene Werte müssen in der CSV-Vorlage eindeutig gekennzeichnet sein.
- Fehlende Werte bleiben leer und werden nicht automatisch als 0 interpretiert.

## 7. Qualitätsanforderungen

- Daten bleiben standardmäßig vollständig lokal.
- Ein fehlerhafter Import verändert den gespeicherten Bestand nicht.
- Die Oberfläche bleibt bei einigen zehntausend Zeilen flüssig.
- Datenbank, Zugangsdaten und persönliche Exporte gelangen nicht in Git.
- Validierung, Berechnung und Duplikatbehandlung sind automatisiert testbar.
- Bedienoberfläche und Fehlermeldungen sind auf Deutsch.

## 8. Minimalistische Architektur

- **Oberfläche:** CustomTkinter auf Tkinter-Basis mit getrennten Dashboard-Seiten.
- **Persistenz:** eine lokale SQLite-Datei mit Tabellen für Importe, Tageswerte und Beitragswerte.
- **Import:** je Quelle eine kleine Spaltenzuordnung auf ein gemeinsames Datenmodell.
- **Auswertung:** SQL-Abfragen und kleine Python-Funktionen; einfache Diagramme zunächst mit Tkinter Canvas.
- **Konfiguration:** lokale JSON-Datei nur für Anzeigeeinstellungen, niemals für Secrets.

Vorgesehene Eindeutigkeitsschlüssel:

- Tageswert: `(quelle, datum)`
- Beitragswert: `(quelle, beitrag_id, datum)`

## 9. Bedienablauf

1. Beim ersten Start `.local.env`, Schlüsseldateien und OAuth-Clients lokal einrichten.
2. Anwendung anschließend normal starten.
3. Das Dashboard öffnet sofort mit den zuletzt gespeicherten Werten.
4. Im Hintergrund werden alle Quellen aktualisiert und einzeln als erfolgreich oder fehlerhaft markiert.
5. Neue Werte und Zeitverläufe erscheinen ohne weitere Eingabe.
6. Bei Bedarf „Jetzt aktualisieren“ verwenden und den detaillierten Systemstatus öffnen oder kopieren.

## 10. Umsetzungsplan

### Phase 0 – Zugänge und Machbarkeitsnachweis

- Instagram-Konto auf Creator oder Business umstellen.
- Developer-Projekte bei Apple, Google, TikTok und Meta anlegen.
- Benötigte Rollen, Scopes und OAuth-Weiterleitungen konfigurieren.
- Je Plattform einen minimalen Testabruf mit dem echten Lucky-Test-Konto durchführen.
- Verfügbare Felder, Datenverzögerung und Kontingente protokollieren.

**Entscheidungstor:** Erst wenn alle vier Testabrufe funktionieren, ist „alles automatisch“ verbindlich erreichbar. Scheitert eine Plattformfreigabe, kann diese Quelle ohne Scraping nicht automatisiert werden.

### Phase 1 – App Store und technischer Kern

- Paketstruktur und Startfenster anlegen.
- SQLite-Schema und Datenzugriff implementieren.
- sichere lokale Konfiguration und Tokenverwaltung anlegen.
- App-Store-Connect-Client und automatischen Startabruf implementieren.
- Abrufstatus, letzte gültige Daten und App-Store-Kennzahlen anzeigen.
- Tests mit gespeicherten Beispielantworten statt echten API-Aufrufen ergänzen.

**Ergebnis:** Ein vollständiger automatischer Ablauf vom Programmstart bis zur Anzeige.

### Phase 2 – YouTube

- Erledigt: OAuth-Verbindung und automatische Token-Erneuerung.
- Erledigt: Kanal- und Analytics-Kennzahlen sowie alle öffentlichen Uploads einschließlich Pagination.
- Erledigt: lokale Snapshots und Anzeige aller Videos im Dashboard.
- Später: Zeitverlauf, Sortierung und gesonderte Top-Videos-Ansicht.

**MVP-Ergebnis:** Beim Programmstart werden App Store und YouTube unabhängig
voneinander aktualisiert. Kanal- und Einzelvideo-Werte bleiben lokal verfügbar,
wenn eine Quelle vorübergehend nicht erreichbar ist.

### Phase 3 – TikTok und Instagram

- Erledigt: TikTok-Desktop-OAuth mit PKCE, Token-Erneuerung, paginierter Abruf
  öffentlicher Videos und lokale Konto-/Video-Snapshots.
- Erledigt: Instagram Business Login über lokalen HTTPS-Callback, langlebige
  Tokens sowie paginierte Konto-, Medien- und medientypabhängige Insights.
- Erledigt: Teilfehler, Token-Erneuerung und erneute Autorisierung behandeln.
- Erledigt: Quellenvergleich und gemeinsame Kennzahlen auf der Startseite.

### Phase 4 – Stabilisierung und Auslieferung

- Erledigt: Fehlerführung, letzte gültige Werte und detaillierter Systemstatus.
- Erledigt: reproduzierbarer Windows-One-folder-Build mit Icon und externen Secrets.
- Erledigt: Nutzerdokumentation und lokale Buildanleitung.
- Später: CSV-Export und komfortable Datenbank-Sicherung.

## 11. Abnahmekriterien für Phase 1

- Start über `python -m lucky_analyzer` funktioniert in der virtuellen Umgebung.
- Der App-Store-Abruf startet automatisch und blockiert die Oberfläche nicht.
- API- und Netzwerkfehler löschen keine bereits gespeicherten Werte.
- Derselbe API-Datenstand erzeugt keine doppelten Snapshots.
- Das Fenster zeigt Downloads, Bewertung, Bewertungsanzahl und letzten erfolgreichen Abruf.
- `python -m unittest` läuft erfolgreich.

## 12. Risiken und Gegenmaßnahmen

| Risiko | Auswirkung | Gegenmaßnahme im MVP |
| --- | --- | --- |
| Instagram-Privatkonto liefert keine Insights-API | Instagram kann nicht automatisch aktualisiert werden | vor Implementierung auf Creator/Business umstellen |
| TikTok oder Meta genehmigen App/Scopes nicht | Quelle bleibt ohne Scraping unzugänglich | Phase-0-Test und ausreichend Zeit für Review einplanen |
| OAuth-Token läuft ab oder wird widerrufen | Abruf fällt aus | Refresh-Token, erneute Anmeldung und klarer Status |
| Plattform-API oder Felddefinition ändert sich | Abruf oder Vergleich bricht | getrennte API-Clients, Versionierung und Vertragstests |
| API-Kontingent wird überschritten | temporär keine neuen Werte | sparsame Abrufe, Caching und Kontingentanzeige |
| Plattformdaten sind verzögert oder aus Datenschutzgründen unvollständig | Dashboard ist nicht sekundengenau | Datenstand und Abdeckungsgrenzen sichtbar anzeigen |
| Lokale Tokens werden entwendet | Zugriff auf Kontodaten | minimale Scopes, keine Secrets in Git, restriktive lokale Speicherung |

## 13. Kostenrahmen

- Python, Tkinter, SQLite und der lokale Betrieb benötigen keine bezahlte Software.
- Ein dauerhaft laufender Server ist für „Abruf beim Start“ nicht nötig.
- Die APIs sind im vorgesehenen kleinen Abrufumfang grundsätzlich ohne nutzungsabhängige Gebühr planbar, unterliegen aber Kontingenten und Plattformregeln.
- Das Apple Developer Program kostet regulär 99 USD pro Jahr; für eine bereits veröffentlichte iOS-App besteht diese Mitgliedschaft üblicherweise ohnehin.
- Creator-/Business-Umstellung bei Instagram ist grundsätzlich kein Hostingposten, kann aber Auswirkungen auf Kontofunktionen und Datenschutz-/Unternehmensangaben haben.
- Nicht kalkulierbar sind eigener Einrichtungsaufwand, mögliche Review-Verzögerungen und zukünftige Preis- oder API-Änderungen der Plattformen.

## 14. Roadmap-Entscheidungen nach dem MVP

Der MVP ist fachlich abgeschlossen. Für spätere Entwicklungsphasen bleiben
folgende Entscheidungen bewusst offen:

1. Welche konkreten Designverbesserungen rechtfertigen einen Toolkit-Wechsel?
2. Welches GUI-Toolkit kann CustomTkinter ersetzen, ohne Datenlogik und lokale
   Windows-Nutzung unnötig zu verkomplizieren?
3. Soll eine private iOS-Anwendung später nativ entwickelt werden oder nur als
   sichere Oberfläche für einen getrennten Datenservice dienen?
4. Welche zusätzlichen Diagramme, Exporte und Zeitvergleiche liefern den größten Nutzen?
