# Anforderungsanalyse und MVP-Plan

## 1. Zielbild

Das Lucky Test Analysetool ist eine lokale Windows-Desktop-Anwendung. Sie bündelt regelmäßig exportierte Kennzahlen der iOS-App und der zugehörigen TikTok-, Instagram- und YouTube-Kanäle. Der Nutzen liegt in einer gemeinsamen, schnell erfassbaren Übersicht statt in vollautomatischer Datenerfassung.

## 2. Nutzer und Kernfragen

Primärer Nutzer ist der Betreiber von Lucky Test. Das Dashboard soll beantworten:

- Wie entwickeln sich Downloads und Bewertungen der App?
- Wie entwickeln sich Reichweite und Interaktionen je Social-Media-Kanal?
- Welche Beiträge erzielen besonders gute Ergebnisse?
- Welche Daten sind aktuell und bei welchen Quellen fehlt ein neuer Import?

## 3. Rahmenbedingungen

- Betrieb lokal unter Windows in VS Code bzw. als später paketierbare Desktop-Anwendung.
- Möglichst keine laufenden Kosten.
- Auf den Social-Media-Plattformen stehen nur normale Privataccounts zur Verfügung.
- Datenzugriffe dürfen nicht von fragilen Scraping- oder Login-Automationen abhängen.
- Der erste MVP benötigt keine Mehrbenutzer-, Cloud- oder Mobilfunktion.

## 4. Datenstrategie

### MVP: manueller CSV-Import

Der Nutzer überträgt Kennzahlen aus den jeweiligen Plattformansichten oder Exporten in definierte CSV-Vorlagen. Das Tool validiert und speichert diese Daten lokal. Dieser Weg ist kostenlos, nachvollziehbar und unabhängig von eingeschränkten APIs für Privataccounts.

Vorgesehene Quellen und Kennzahlen:

| Quelle | Kennzahlen im MVP | Granularität |
| --- | --- | --- |
| App Store | Downloads, Updates, Bewertung, Bewertungsanzahl | Tag |
| TikTok | Aufrufe, Likes, Kommentare, Shares | Beitrag und Stichtag |
| Instagram | Aufrufe/Reichweite, Likes, Kommentare | Beitrag und Stichtag |
| YouTube | Aufrufe, Likes, Kommentare | Video und Stichtag |

Jeder Import benötigt mindestens `datum`, `quelle` und die zur Quelle passenden numerischen Felder. Beitragsdaten erhalten zusätzlich eine stabile `beitrag_id` und optional `titel` sowie `url`.

### Später prüfbare Automatisierung

- App Store Connect API, falls ein passender Apple-Zugang und API-Schlüssel vorhanden sind.
- Offizielle Plattform-APIs nur, wenn Accounttyp, Freigaben und kostenlose Kontingente dies erlauben.
- Kein HTML-Scraping als regulärer Datenweg.

## 5. Funktionale Anforderungen

### Muss im MVP

1. CSV-Datei auswählen und Quelle zuordnen.
2. Pflichtspalten, Datumswerte und Zahlen prüfen; verständliche Fehler anzeigen.
3. Gültige Datensätze idempotent in SQLite speichern, damit erneuter Import keine Duplikate erzeugt.
4. Dashboard mit aktuellem Stand pro Quelle anzeigen.
5. Entwicklung eines auswählbaren Zeitraums darstellen.
6. Top-Beiträge nach Aufrufen und Interaktionsrate anzeigen.
7. Datum des letzten erfolgreichen Imports pro Quelle zeigen.
8. Lokale Daten als CSV exportieren.

### Soll nach dem MVP

- Vergleich frei wählbarer Zeiträume.
- Filter nach Plattform und Beitrag.
- Automatischer App-Store-Import über offizielle API.
- Paketierung als Windows-EXE.

### Bewusst nicht im MVP

- Automatische Social-Media-Anmeldung oder Scraping.
- Cloud-Synchronisation und Mehrbenutzerbetrieb.
- KI-/NLP-Auswertungen oder automatische Repository-Analyse.
- Benachrichtigungen, Kampagnenplanung oder Posting-Funktionen.

## 6. Qualitätsanforderungen

- Daten bleiben standardmäßig vollständig lokal.
- Ungültige Dateien verändern den gespeicherten Datenbestand nicht.
- Die Oberfläche ist bei üblichen Datenmengen von einigen zehntausend Zeilen flüssig.
- Fehlermeldungen nennen Datei, Zeile und betroffenes Feld.
- Datenbank und Exportdateien werden nicht in Git eingecheckt.
- Die Kernlogik für Validierung und Kennzahlen ist automatisiert testbar.

## 7. Minimalistische Architektur

- **Oberfläche:** Tkinter mit Seiten für Dashboard, Import und Datenbestand.
- **Persistenz:** eine lokale SQLite-Datei; Tabellen für Importe, Tageskennzahlen und Beiträge.
- **Import:** je Quelle eine kleine Spaltenzuordnung auf ein gemeinsames internes Datenmodell.
- **Auswertung:** SQL-Abfragen und kleine Python-Funktionen; einfache Diagramme zunächst mit Tkinter Canvas.
- **Konfiguration:** lokale JSON-Datei nur für Anzeigeeinstellungen, niemals für Secrets.

Geplante Eindeutigkeitsschlüssel:

- Tageswert: `(quelle, datum)`
- Beitragswert: `(quelle, beitrag_id, datum)`

## 8. Bedienablauf

1. Anwendung starten.
2. Unter „Import“ Quelle und CSV-Datei wählen.
3. Vorschau und Validierungsergebnis prüfen.
4. Import bestätigen.
5. Dashboard aktualisiert Kennzahlen und Importstatus.
6. Bei Bedarf gefilterte Daten exportieren.

## 9. Umsetzungsplan

### Phase 1 – lauffähiger Kern

- Paketstruktur und Startfenster anlegen.
- SQLite-Schema und Datenzugriff implementieren.
- Eine dokumentierte Beispiel-CSV für App-Store-Tageswerte bereitstellen.
- Validierung, Importvorschau und idempotenten Import umsetzen.
- Aktuelle App-Store-Kennzahlen tabellarisch anzeigen.
- Unit-Tests für Validierung und Duplikatbehandlung ergänzen.

**Ergebnis:** Ein vollständiger vertikaler Ablauf von CSV bis Anzeige.

### Phase 2 – Social Media und Dashboard

- CSV-Profile für TikTok, Instagram und YouTube ergänzen.
- Kennzahlenkarten, Zeitverlauf und Top-Beiträge erstellen.
- Zeitraum- und Quellenfilter ergänzen.

### Phase 3 – Nutzbarkeit und Auslieferung

- CSV-Export und Datenbank-Sicherung ergänzen.
- Fehlerführung und leere Zustände überarbeiten.
- Windows-Paketierung prüfen und Nutzerdokumentation vervollständigen.

## 10. Abnahmekriterien für Phase 1

- Start über `python -m lucky_analyzer` funktioniert in der virtuellen Umgebung.
- Eine gültige Beispiel-CSV wird ohne externe Abhängigkeiten importiert.
- Fehlerhafte Datums- oder Zahlenwerte werden mit Zeilenbezug abgelehnt.
- Derselbe Import verdoppelt keine Datensätze.
- Das Fenster zeigt aktuelle Downloads, Bewertung, Bewertungsanzahl und letzten Import.
- Automatisierte Tests laufen mit `python -m unittest` erfolgreich.

## 11. Offene fachliche Entscheidungen

Vor Phase 1 sollten nur diese Punkte bestätigt werden:

1. Welche App-Store-Exportansicht steht tatsächlich zur Verfügung und welche Spalten enthält sie?
2. Welche Kennzahl bedeutet intern „Downloads“: Erstdownloads, Gesamtdownloads oder App Units?
3. Werden Social-Media-Werte regelmäßig pro Beitrag erfasst oder reicht zunächst ein täglicher Kanalgesamtstand?
4. Welche Zeiträume sind im Dashboard am wichtigsten (zum Beispiel 7, 30 und 90 Tage)?

Diese Fragen blockieren die technische Grundstruktur nicht, beeinflussen aber CSV-Vorlagen und Dashboard-Beschriftungen.
