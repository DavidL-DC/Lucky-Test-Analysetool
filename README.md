# Lucky Test Analysetool

Lokales Analyse-Dashboard für die iOS-App **Lucky Test**. Es soll App-Store- und Social-Media-Kennzahlen aus TikTok, Instagram und YouTube übersichtlich zusammenführen.

## Projektstand

Phase 1 ist als lokaler App-Store-Kern umgesetzt. Beim Start fordert das Tool die neuesten verfügbaren App-Store-Analytics-Berichte an, speichert Tageswerte in SQLite und zeigt den letzten gültigen Stand. Umfang, Datenstrategie und weitere MVP-Schritte stehen in der [Anforderungsanalyse](ANFORDERUNGSANALYSE.md).

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

Abhängigkeiten und das lokale Paket installieren:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

Konfigurationsvorlage kopieren:

```powershell
Copy-Item .local.env.example .local.env
```

Danach in `.local.env` Issuer ID, Key ID, Apple App ID und Bundle ID eintragen. Die P8-Datei unter dem dort angegebenen Pfad ablegen, standardmäßig:

```text
.secrets/AuthKey_LuckyTest.p8
```

`.local.env` und der Inhalt von `.secrets/` sind von Git ausgeschlossen.

Anwendung starten:

```powershell
.\.venv\Scripts\python.exe -m lucky_analyzer
```

Beim ersten erfolgreichen API-Aufruf legt Apple gegebenenfalls eine neue fortlaufende Analytics-Report-Anfrage an. Bis die ersten Berichte verfügbar sind, können ein bis zwei Tage vergehen.

Tests ausführen:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Kennzahlen in Phase 1

- Erstdownloads, erneute Downloads, Gesamtdownloads und Updates
- Installationen und Deinstallationen mit sichtbarem Datenschutzhinweis
- letzter erfolgreicher Abruf und Datenstand
- Bewertung und Bewertungsanzahl sind im Datenmodell vorbereitet, bleiben aber leer, bis ein belastbarer offizieller Datenweg bestätigt ist
