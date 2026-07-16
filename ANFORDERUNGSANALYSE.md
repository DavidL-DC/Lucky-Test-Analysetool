# Anforderungsanalyse und MVP-Plan

## 1. Zielbild

Das Lucky Test Analysetool ist eine lokale Windows-Desktop-Anwendung. Sie bündelt regelmäßig erfasste Kennzahlen der iOS-App und der zugehörigen TikTok-, Instagram- und YouTube-Kanäle. Der unmittelbare Nutzen ist eine gemeinsame, schnell erfassbare Übersicht statt einer vollautomatischen Datenerfassung.

## 2. Nutzer und Kernfragen

Primärer Nutzer ist der Betreiber von Lucky Test. Das Dashboard soll beantworten:

- Wie entwickeln sich Downloads und Bewertungen der App?
- Wie entwickeln sich Reichweite und Interaktionen je Social-Media-Kanal?
- Welche Beiträge erzielen besonders gute Ergebnisse?
- Wie aktuell sind die Daten und bei welcher Quelle fehlt ein neuer Import?

## 3. Rahmenbedingungen und Abgrenzung

- Betrieb lokal unter Windows in VS Code, später optional als Desktop-Paket.
- Möglichst keine laufenden Kosten.
- Für Social Media stehen nur normale Privataccounts zur Verfügung.
- Der MVP hängt nicht von eingeschränkten APIs, Scraping oder Login-Automationen ab.
- Keine Cloud-, Mehrbenutzer-, Posting-, Benachrichtigungs- oder KI-Funktionen im MVP.

## 4. Datenstrategie

### MVP: manueller CSV-Import

Der Nutzer überträgt Kennzahlen aus den jeweiligen Plattformansichten oder verfügbaren Exporten in definierte CSV-Vorlagen. Das Tool validiert und speichert diese Daten lokal. So bleibt der Datenweg kostenlos, nachvollziehbar und unabhängig von API-Berechtigungen für Privataccounts.

| Quelle | Kennzahlen im MVP | Granularität |
| --- | --- | --- |
| App Store | Downloads, Updates, Bewertung, Bewertungsanzahl | Tag |
| TikTok | Aufrufe, Likes, Kommentare, Shares | Beitrag und Stichtag |
| Instagram | Aufrufe/Reichweite, Likes, Kommentare | Beitrag und Stichtag |
| YouTube | Aufrufe, Likes, Kommentare | Video und Stichtag |

Jede Zeile benötigt mindestens `datum`, `quelle` und die passenden numerischen Felder. Beitragsdaten erhalten zusätzlich `beitrag_id` sowie optional `titel` und `url`.

### Später prüfbare Automatisierung

- App Store Connect API, falls ein geeigneter Zugang und API-Schlüssel vorhanden sind.
- Offizielle Plattform-APIs nur nach Prüfung von Accounttyp, Berechtigungen und Kosten.
- HTML-Scraping bleibt ausgeschlossen.

## 5. Funktionale Anforderungen

### Muss im MVP

1. CSV-Datei auswählen und Quelle zuordnen.
2. Pflichtspalten, Datumswerte und Zahlen prüfen und Fehler mit Zeilenbezug anzeigen.
3. Eine Vorschau anzeigen, bevor Daten gespeichert werden.
4. Gültige Datensätze idempotent in SQLite speichern; erneuter Import erzeugt keine Duplikate.
5. Aktuellen Stand und letzten erfolgreichen Import pro Quelle anzeigen.
6. Entwicklung in einem auswählbaren Standardzeitraum darstellen.
7. Top-Beiträge nach Aufrufen und Interaktionsrate anzeigen.
8. Gespeicherte Daten wieder als CSV exportieren.

### Soll nach dem MVP

- frei wählbare Zeiträume und Zeitvergleiche
- Filter nach Plattform und Beitrag
- automatischer App-Store-Import über eine offizielle API
- Paketierung als Windows-EXE

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

- **Oberfläche:** Tkinter mit Dashboard, Import und Datenbestand.
- **Persistenz:** eine lokale SQLite-Datei mit Tabellen für Importe, Tageswerte und Beitragswerte.
- **Import:** je Quelle eine kleine Spaltenzuordnung auf ein gemeinsames Datenmodell.
- **Auswertung:** SQL-Abfragen und kleine Python-Funktionen; einfache Diagramme zunächst mit Tkinter Canvas.
- **Konfiguration:** lokale JSON-Datei nur für Anzeigeeinstellungen, niemals für Secrets.

Vorgesehene Eindeutigkeitsschlüssel:

- Tageswert: `(quelle, datum)`
- Beitragswert: `(quelle, beitrag_id, datum)`

## 9. Bedienablauf

1. Anwendung starten.
2. Unter „Import“ Quelle und CSV-Datei wählen.
3. Vorschau und Validierungsergebnis prüfen.
4. Import bestätigen.
5. Dashboard zeigt aktualisierte Kennzahlen und Importstatus.
6. Bei Bedarf gefilterte Daten exportieren.

## 10. Umsetzungsplan

### Phase 1 – vertikaler Kern

- Paketstruktur und Startfenster anlegen.
- SQLite-Schema und Datenzugriff implementieren.
- Dokumentierte Beispiel-CSV für App-Store-Tageswerte bereitstellen.
- Validierung, Vorschau und idempotenten Import umsetzen.
- Aktuelle App-Store-Kennzahlen tabellarisch anzeigen.
- Unit-Tests für Validierung und Duplikatbehandlung ergänzen.

**Ergebnis:** Ein vollständiger Ablauf von CSV-Auswahl bis Anzeige.

### Phase 2 – Social Media und Dashboard

- CSV-Profile für TikTok, Instagram und YouTube ergänzen.
- Kennzahlenkarten, Zeitverlauf und Top-Beiträge erstellen.
- Zeitraum- und Quellenfilter ergänzen.

### Phase 3 – Nutzbarkeit und Auslieferung

- CSV-Export und Datenbank-Sicherung ergänzen.
- Fehlerführung und leere Zustände überarbeiten.
- Windows-Paketierung prüfen und Nutzerdokumentation vervollständigen.

## 11. Abnahmekriterien für Phase 1

- Start über `python -m lucky_analyzer` funktioniert in der virtuellen Umgebung.
- Eine gültige Beispiel-CSV wird ohne externe Abhängigkeiten importiert.
- Fehlerhafte Datums- oder Zahlenwerte werden mit Zeilenbezug abgelehnt.
- Derselbe Import verdoppelt keine Datensätze.
- Das Fenster zeigt Downloads, Bewertung, Bewertungsanzahl und letzten Import.
- `python -m unittest` läuft erfolgreich.

## 12. Risiken und Gegenmaßnahmen

| Risiko | Auswirkung | Gegenmaßnahme im MVP |
| --- | --- | --- |
| Plattformen bieten für Privataccounts keine geeigneten Exporte | Daten müssen manuell übertragen werden | feste CSV-Vorlagen mit verständlicher Anleitung |
| Kennzahlen heißen je Plattform unterschiedlich | falsche Vergleiche | Quellfelder dokumentieren und intern normalisieren |
| Kumulative Werte werden mit Tageswerten verwechselt | irreführende Trends | Wertart in Vorlage und Oberfläche sichtbar machen |
| Plattformansichten ändern sich | Importvorlage passt nicht mehr | kleine, getrennte Quellprofile und klare Validierungsfehler |
| Manuelle Erfassung ist unregelmäßig | Lücken im Verlauf | letzten Import und Datenlücken deutlich anzeigen |

## 13. Offene fachliche Entscheidungen

Diese Fragen blockieren die technische Grundstruktur nicht, müssen aber vor den jeweiligen Importprofilen bestätigt werden:

1. Welche App-Store-Exportansicht steht tatsächlich zur Verfügung und welche Spalten enthält sie?
2. Bedeutet „Downloads“ Erstdownloads, Gesamtdownloads oder App Units?
3. Werden Social-Media-Werte regelmäßig pro Beitrag erfasst oder genügt zunächst ein täglicher Kanalgesamtstand?
4. Welche Standardzeiträume sind am wichtigsten, beispielsweise 7, 30 und 90 Tage?
5. Sollen Reichweite und Aufrufe getrennt oder als plattformspezifische Hauptkennzahl gezeigt werden?
