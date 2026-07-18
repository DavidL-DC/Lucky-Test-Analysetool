# Projektregeln

## Ziel

Den abgeschlossenen lokalen MVP für das Lucky-Test-Analyse-Dashboard stabil
halten und spätere Erweiterungen klein, sicher und nachvollziehbar umsetzen.

## Technische Leitplanken

- Python 3.11+ und Windows/VS Code unterstützen.
- Standardbibliothek bevorzugen; neue Dependencies nur mit konkreter Begründung ergänzen.
- Für den MVP Tkinter, SQLite und CSV verwenden.
- Kleine, sprechend benannte Funktionen und Module schreiben.
- Deutsche Oberflächentexte mit echten Umlauten und ß verfassen.
- Zugangsdaten, Tokens, Exporte und lokale Datenbanken nicht committen.
- Keine Social-Media-Seiten scrapen und keine inoffiziellen Login-Automationen einbauen.

## Arbeitsweise

- Bestehende Nutzeränderungen erhalten.
- Änderungen klein und thematisch fokussiert halten.
- Vor Abschluss mindestens Syntaxprüfung und relevante Tests ausführen.
- README und Anforderungsanalyse aktualisieren, wenn sich Bedienung oder Umfang ändern.

## Vorgesehene Struktur ab Implementierungsphase

```text
src/
  lucky_analyzer/
    app.py
    database.py
    importers.py
    models.py
tests/
```
