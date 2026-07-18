# Lucky Test Analysetool

Lokales Analyse-Dashboard für die iOS-App **Lucky Test**. Es soll App-Store- und Social-Media-Kennzahlen aus TikTok, Instagram und YouTube übersichtlich zusammenführen.

## Projektstand

Der lokale App-Store-Kern und die erste YouTube-Integration sind umgesetzt. Beim Start ruft das Tool beide Quellen automatisch ab, speichert die Werte in SQLite und zeigt bei Fehlern weiterhin den letzten gültigen Stand.

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
- CustomTkinter auf Tkinter-Basis, SQLite und HTTP-Zugriffe auf offizielle APIs
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

### YouTube einrichten

In der Google Cloud Console müssen **YouTube Data API v3** und **YouTube Analytics API** aktiviert sein. Den OAuth-Client als Anwendungstyp **Desktop-App** herunterladen und hier ablegen:

```text
.secrets/youtube_oauth_client.json
```

Beim ersten Start öffnet sich die Google-Anmeldung im Standardbrowser. Mit dem als Testnutzer eingetragenen Kanalkonto anmelden und den reinen Lesezugriff bestätigen. Das Tool speichert anschließend ausschließlich lokal ein Token unter `.secrets/youtube_token.json`. Im OAuth-Testmodus ist nach sieben Tagen üblicherweise eine erneute Anmeldung erforderlich.

Anwendung starten:

```powershell
.\.venv\Scripts\python.exe -m lucky_analyzer
```

Beim ersten erfolgreichen API-Aufruf legt Apple gegebenenfalls eine neue fortlaufende Analytics-Report-Anfrage an. Bis die ersten Berichte verfügbar sind, können ein bis zwei Tage vergehen.

Tests ausführen:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Windows-Build erstellen

Die Build-Abhängigkeiten einmalig installieren:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
```

Danach den reproduzierbaren One-folder-Build starten. Der CMD-Starter umgeht
nur für diesen Buildprozess eine möglicherweise restriktive
PowerShell-Ausführungsrichtlinie:

```powershell
.\build_windows.cmd
```

Die fertige Anwendung liegt anschließend hier:

```text
dist/Lucky Test Analysetool/Lucky Test Analysetool.exe
```

Zugangsdaten werden nicht in die EXE eingebettet. Vor dem ersten Start müssen
die vorhandene `.local.env` und der Ordner `.secrets` neben die EXE kopiert
werden. Die lokale Datenbank wird im Unterordner `data` angelegt. Bei einem
späteren Update sollten `.local.env`, `.secrets` und `data` erhalten bleiben.

```powershell
Copy-Item .local.env "dist\Lucky Test Analysetool\.local.env"
Copy-Item .secrets "dist\Lucky Test Analysetool\.secrets" -Recurse -Force
```

Der Build ist bewusst ein Ordner und keine einzelne Datei. Das verbessert die
Zuverlässigkeit von Tkinter/CustomTkinter und verkürzt den Programmstart. Für
eine Weitergabe muss der vollständige Ordner kopiert werden.

## Kennzahlen in Phase 1

- Erstdownloads, erneute Downloads, Gesamtdownloads und Updates
- Installationen und Deinstallationen mit sichtbarem Datenschutzhinweis
- letzter erfolgreicher Abruf und Datenstand
- automatische Speicherung schriftlicher App-Store-Rezensionen
- Anzahl und Sterndurchschnitt der schriftlichen Rezensionen; bewusst getrennt von Apples offizieller Gesamtbewertung
- 1–5-Sterne-Verteilung der schriftlichen Rezensionen sowie auswählbare vollständige Rezensionstexte
- gemeinsame DACH-Gesamtbewertung für Deutschland, Österreich und die Schweiz über Apples öffentlichen Lookup; länderweise Bewertungszahlen werden addiert und der Durchschnitt entsprechend gewichtet

## Oberfläche

Das Dashboard verwendet eine iOS-inspirierte Glasoptik mit abgerundeten Karten, klarer Informationshierarchie und einer responsiven Scrollansicht. Über den Schalter in der Seitenleiste kann jederzeit zwischen einem anthrazitfarbenen Dark Mode und einem weiß-hellgrauen Light Mode gewechselt werden. Die lokal installierte Schrift Quicksand sorgt für eine runde, freundliche Typografie. Rezensionen lassen sich in einer kompakten Liste auswählen und vollständig lesen oder kopieren.

Unterhalb der zentralen Zeitraumwahl trennt eine zweite Navigation die Inhalte in
**Start**, **App Store**, **YouTube**, **TikTok** und **Instagram**. Beim Wechsel
bleibt der gewählte Zeitraum erhalten und der Inhaltsbereich beginnt wieder oben.
Die Startseite bündelt Downloads, DACH-Bewertung und Bewertungsanzahl,
Sterneverteilung schriftlicher Rezensionen, Follower und Abonnenten,
Videoaufrufe, Video-Likes, Kommentare, veröffentlichte Videos sowie den jüngsten
Datenstand aller verbundenen Quellen.

Das kompakte Datenquellen-Kästchen unten links ist anklickbar. Es öffnet den
detaillierten Systemstatus mit den Zuständen aller vier Quellen, der letzten
Systemmeldung und einer Kopierfunktion für Support und Fehlersuche.

Das Lucky-Test-Symbol liegt zentral unter `assets/icon.png`, ersetzt den
„LT“-Platzhalter in der Seitenleiste und wird für das Hauptfenster sowie den
detaillierten Systemstatus als Fenstericon verwendet. Unter Windows setzt die
Anwendung zusätzlich eine eigene App-Identität, damit nicht das allgemeine
Python-Icon verwendet wird. Die daraus erzeugte Windows-Variante liegt unter
`assets/icon.ico`.
Fehlt die Datei in einer lokalen Kopie, startet das Tool weiterhin mit dem
Standardicon des Betriebssystems.

Hauptinhalt und Seitenleiste besitzen voneinander unabhängige Scrollbereiche.
Dadurch bleiben Navigation, Quellenstatus und Darstellungsumschaltung auch bei
kleineren Fensterhöhen erreichbar. Video-, Medien-, Rezensions- und Statuslisten
scrollen weiterhin innerhalb ihres eigenen Bereichs, ohne die Hauptseite
mitzubewegen.

Die zentrale Zeitraumwahl bietet **7 Tage**, **30 Tage**, **90 Tage** und
**Gesamt**. App-Store-Ereignisse und datierte schriftliche Rezensionen werden
direkt gefiltert. Für kumulative Bewertungen, Follower, Aufrufe, Likes,
Kommentare und weitere Social-Media-Zähler speichert jeder Abruf einen lokalen
Snapshot. Sobald ein ausreichend alter Vergleichspunkt vorhanden ist, zeigt das
Dashboard den im Zeitraum gemessenen Zuwachs mit `+` an. Bis dahin bleibt der
aktuelle Wert sichtbar und wird mit `gesamt` gekennzeichnet. Frühere Zeiträume
vor dem ersten lokalen Snapshot können die Plattform-APIs nicht rückwirkend
rekonstruieren.

## YouTube-Kennzahlen

- Kanal: Abonnenten, Aufrufe, Videoanzahl, summierte Likes und Kommentare
- Watchtime und durchschnittliche Wiedergabedauer aus der YouTube Analytics API
- alle öffentlichen Uploads mit Aufrufen, Likes, Kommentaranzahl, Watchtime und Wiedergabedauer
- automatische Pagination und lokale Speicherung des letzten erfolgreichen Stands
- keine Einnahmen, Werbeumsätze oder Kommentartexte im aktuellen MVP

## TikTok einrichten

Die TikTok-Developer-App benötigt im Sandbox-Modus Login Kit für **Desktop**, die
Redirect-URI `http://127.0.0.1:3456/callback/` sowie die Scopes
`user.info.profile`, `user.info.stats` und `video.list`. Das verwendete TikTok-Konto
muss als Target User eingetragen sein. Client Key und Client Secret ausschließlich
lokal in `.local.env` eintragen:

```text
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
```

Beim ersten Start öffnet sich die TikTok-Anmeldung im Browser. Das Zugriffstoken
wird unter `.secrets/tiktok_token.json` gespeichert und automatisch erneuert.
Angezeigt werden Follower, öffentliche Videoanzahl sowie die summierten Aufrufe,
Likes, Kommentare und Shares aller öffentlichen Videos. Dieselben Werte werden
zusätzlich je Video aufgeführt. „Folgt“ und TikToks redundanter Konto-Like-Zähler
werden im Dashboard bewusst nicht angezeigt. Watchtime und Kommentartexte stellt
die Display API nicht bereit.

## Instagram einrichten

Die Meta-App verwendet **Instagram API with Instagram Login** mit den
Berechtigungen `instagram_business_basic` und
`instagram_business_manage_insights`. Als Business-Login-Weiterleitung ist
`https://localhost:3457/callback/` hinterlegt. Instagram App ID und App Secret
ausschließlich lokal in `.local.env` eintragen:

```text
INSTAGRAM_APP_ID=...
INSTAGRAM_APP_SECRET=...
```

Beim ersten Login erzeugt das Tool ein selbstsigniertes localhost-Zertifikat in
`.secrets/`. Der Browser zeigt deshalb möglicherweise einmalig eine
Zertifikatswarnung; über **Erweitert → Weiter zu localhost** kann der lokale
Callback geöffnet werden. Das gespeicherte langlebige Token wird automatisch
rechtzeitig erneuert.

Angezeigt werden Profil-, Follower- und Medienzahlen, Konto-Insights der letzten
30 Tage sowie Likes, Kommentare, Aufrufe, Reichweite, Speicherungen, Shares und
– soweit Meta sie für den Medientyp liefert – Reel-Watchtime je Medium. Nicht
verfügbare Insights werden als `–` dargestellt.
