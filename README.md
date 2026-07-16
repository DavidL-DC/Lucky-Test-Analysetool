# Lucky Test Analysetool

Lokales Analyse-Dashboard für die iOS-App **Lucky Test**. Es soll App-Store- und Social-Media-Kennzahlen aus TikTok, Instagram und YouTube übersichtlich zusammenführen.

## Projektstand

Das Projekt befindet sich in der Anforderungs- und Planungsphase. Umfang, Datenstrategie, Risiken und MVP-Schritte stehen in der [Anforderungsanalyse](ANFORDERUNGSANALYSE.md).

## Geplanter MVP

- lokale Desktop-Anwendung für Windows
- automatischer Abruf beim Programmstart für App Store, TikTok, Instagram und YouTube
- einmalige geführte Einrichtung der offiziellen API-Zugänge
- Speicherung in einer lokalen SQLite-Datenbank
- Dashboard mit aktuellen Kennzahlen, Zeitverlauf und Kanalvergleich
- sichtbarer Aktualisierungsstatus je Quelle und Weiterverwendung der letzten gültigen Daten bei API-Fehlern
- keine inoffiziellen Login-Automationen und kein Scraping

## Technische Basis

- Python 3.11 oder neuer
- Tkinter, SQLite und HTTP-Zugriffe auf offizielle APIs
- Zugangsdaten ausschließlich lokal und außerhalb von Git

## Voraussetzungen für automatische Abrufe

- aktives App-Store-Connect-Konto mit geeignetem API-Schlüssel
- Google-Cloud-Projekt und YouTube-OAuth-Freigabe
- TikTok-Developer-App mit freigeschalteter Display API und OAuth
- Instagram-Konto vom Typ Creator oder Business; ein normales Privatkonto liefert keine offiziellen Insights

Die lokale Anwendung kann ohne laufende Hostingkosten betrieben werden. Plattformkonten, Freigabeverfahren, API-Änderungen und mögliche spätere Kontingentkosten bleiben externe Abhängigkeiten. Details stehen in der [Anforderungsanalyse](ANFORDERUNGSANALYSE.md).

## Entwicklungsumgebung

Virtuelle Umgebung in PowerShell aktivieren:

```powershell
.\.venv\Scripts\Activate.ps1
```

Aktuell gibt es noch keinen Startbefehl, da diese Projektphase ausschließlich Analyse und Planung umfasst.
