# Feature Usage Analyse

Streamlit-Dashboard zur Analyse der Feature-Nutzung pro Schule, gespeist aus vorberechneten Snapshots der `klapp-prod` MongoDB.

Für das reine Anzeigen des Dashboards ist **keine** Datenbankverbindung nötig, solange `data/` bereits Snapshots enthält.

## Voraussetzungen

- Python 3.10 oder neuer
- (nur für neue Snapshots) Zugriff auf die Klapp-MongoDB

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## App starten

Immer aus dem Projekt-Hauptordner starten (die Datenpfade `data/...` sind relativ dazu):

```bash
streamlit run app.py
```

Die App öffnet sich unter <http://localhost:8501>.

## Umgebungsvariablen (.env)

Nur nötig, um Snapshots neu zu erzeugen. `.env.example` nach `.env` kopieren und Werte eintragen:

```bash
cp .env.example .env
```

Die `.env` enthält Zugangsdaten und ist **nicht** im Repo enthalten.

## Snapshot aktualisieren (optional)

Das Snapshot-Skript schreibt nach `../data/`, muss also aus dem Ordner `lib/` gestartet werden:

```bash
cd lib
python Feature_snapshot.py   # -> data/snapshot.parquet, data/mother_daughter.json, data/class_precentage.parquet
cd ..
```

## Projektstruktur

```
app.py                 Einstiegspunkt für Streamlit
pages/                 Dashboard-Seite (Feature-Usage Analyse)
lib/                   Pipelines, Helper und Snapshot-Skript
data/                  Parquet-/JSON-Snapshots (nicht im Repo, siehe .gitignore)
docs/                  Beispiel-Screenshots (mit Testdaten)
```

## Beispiel-Screenshots

Screenshots mit Testdaten (`docs/`):

![Gesamtübersicht](docs/overview.png)
![Feature-Analyse](docs/feature_view.png)
![Schule im Detail](docs/detailed_view.png)

## Hinweise

- Zeiträume in den Aggregationen: 30 Tage, 90 Tage, letztes Schuljahr, gesamte Historie.
- `data/` wird nie committet (siehe `.gitignore`) – die Snapshots enthalten echte Schuldaten.
