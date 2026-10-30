# Skripte

Mess-Skripte zu den Befunden dieses Ordners. Jede Regel wird mechanisch nachgebaut und
gegen einen **blinden Einstieg** in dieselben Titel im selben Zeitraum gemessen.
Kommentare und Ausgaben sind deutsch. Lizenz: MIT (siehe `../LICENSE`, Teil A).

Rohdaten liegen **nicht** im Repo: Kursdaten von Yahoo dürfen nicht weiterverteilt werden.
Jedes Skript lädt selbst oder liest einen lokalen Datenordner (Format unten). Was die
Skripte schreiben (`daten/`, `ergebnisse/`, `*.json`, `*.npz`, `*.parquet`), hält
`../.gitignore` aus Git heraus.

## Abhängigkeiten

Python ≥ 3.10.

| Ordner | Pakete |
|---|---|
| `faktor-rotation/` | `numpy`, `pandas`, `pyarrow`, `scipy`, `yfinance`, `requests` |
| `einbrueche/`, `rebalancing/` | `numpy` |

```bash
python -m venv .venv && .venv/bin/pip install numpy pandas pyarrow scipy yfinance requests
```

## faktor-rotation/ — Faktor-Rotation gegen Gleichgewicht

Sechs Faktor-ETFs (VLUE, QUAL, MTUM, IWF, USMV, SIZE) gegen SPY. Monatliche Rotation
nach relativer Stärke, gemessen gegen die Gleichgewichtung derselben sechs ETFs (W0).

| Skript | misst / tut |
|---|---|
| `01_daten.py` | lädt die sieben ETFs ab 2013 (yfinance, `auto_adjust=True`), friert sie als Parquet ein und hasht sie. `--verify` prüft den Hash, `--force` lädt neu (= neues Experiment). |
| `01b_riskfree.py` | risikofreier Zins DGS3MO von FRED, eigene Datei mit eigenem Hash. Braucht die Umgebungsvariable `FRED_API_KEY` (kostenloser Schlüssel bei FRED). |
| `02_signal.py` | RRG-Kern: z-Score des Verhältnisses Faktor/SPY (252 Tage), optional mit Momentum-Achse. |
| `03_backtest.py` | 42 Konfigurationen (2 Scores × 7 Gewichtungen × 3 Overlays): Signal am Monatsletzten, Einstieg zum Open des Folgetags, driftende Gewichte, 0,10 % Kosten auf den umgesetzten Turnover. |
| `04_kennzahlen.py` | CAGR, Sharpe, Sortino, MaxDD; Information Ratio gegen W0 mit demselben Overlay, als Gitter. |
| `08_schwelle.py` | Nullverteilung der Sharpe-Differenz per Permutation der Score-Zuordnung: welche Schwelle wäre datengestützt gewesen? |
| `05_overfitting.py` | Deflated Sharpe Ratio und PBO (CSCV, 16 Blöcke) auf den Excess-Renditen gegen W0. |
| `06_montecarlo.py` | stationärer Block-Bootstrap auf dem Faktor-Panel (Regel läuft auf jedem Pfad neu) und Permutationstest, auf Monatsbasis. |
| `07_walkforward.py` | Walk-Forward: Train 60 Monate → Embargo 1 Monat → Test 12 Monate. |

Aufruf, im Ordner `faktor-rotation/`:

```bash
python 01_daten.py && python 01b_riskfree.py && python 02_signal.py \
  && python 03_backtest.py && python 04_kennzahlen.py && python 08_schwelle.py \
  && python 05_overfitting.py && python 07_walkforward.py && python 06_montecarlo.py
```

**Datenstand des Befunds** (Lauf 2026-07-25):

- ETF-Panel: 2013-01-02 → 2026-07-23, 3409 Handelstage, `daten/faktor_panel.parquet`,
  SHA-256 (in Vierergruppen, ohne Leerzeichen zusammensetzen):
  `8181 a545 831b 6351 f5d9 60a4 1811 51e0 29ab 5d61 fe02 5e43 65ca 9e87 cfba 8290`
- DGS3MO: 2013-01-02 → 2026-07-23, 3537 Werte, `daten/riskfree.parquet`,
  SHA-256: `7831 6f65 a2df d499 8e46 804b ad5d e1ad 9094 f4ba 730e ec28 64f2 5bd6 a987 b9e6`

yfinance rechnet Ausschüttungen rückwirkend in die Reihe. Ein Download heute ergibt
einen anderen Hash und damit ein neues Experiment, nicht denselben Lauf.

## einbrueche/ — Warnt der Bruch der 150-Tage-Linie vor schweren Einbrüchen?

| Skript | misst |
|---|---|
| `01_vorwarnung.py` | jede Episode mit Drawdown ≤ −60 % vom 252-Tage-Hoch: Wie viel Verlust war beim letzten Bruch der EMA150 schon gelaufen, wie viele Handelstage vorher kam er? |
| `02_basisrate.py` | Gegenrichtung: Von allen EMA150-Brüchen, wie viele führen binnen 252 Handelstagen auf ≤ −40 % bzw. ≤ −60 %? (Fehlalarmquote) |

## rebalancing/ — Gleichgewicht + wöchentliches Rebalancing gegen Buy & Hold

| Skript | misst / tut |
|---|---|
| `01_matrix.py` | baut die Wochen-Kursmatrix (Wochenschluss = letzter Handelstag je ISO-Woche) → `wochen.npz`. |
| `02_gleichgewicht.py` | Zufallskörbe (10/20 Titel, 26–260 Wochen, 5000 je Zelle): Gleichgewicht wöchentlich zurückgesetzt gegen Buy & Hold, netto nach 0,10 % Kosten → `basis.npz`. |
| `03_woher.py` | (A) gemeinsame Zeit-Permutation aller Titel: Timing oder Diversification Return? (B) eingestreute Totalverluste: ab welcher Rate kippt der Vorteil? |
| `04_gewichtung.py` | Gewichtung gleich / invers ADR / nach ADR (20-Tage-Spanne, nur Vergangenheit). |
| `05_kipppunkt.py` | Kipppunkt der Totalverlust-Rate je Gewichtung. |
| `06_pleite_trifft_volatile.py` | Pleite zufällig gegen Pleite bei den volatilsten Titeln (wird in 07 korrigiert). |
| `07_pleite_korrigiert.py` | wie 06, aber mit gleicher erwarteter Zahl an Pleiten (`p_eff = p · n/k`). |

Aufruf: `python 01_vorwarnung.py`, `python 02_basisrate.py` bzw. in `rebalancing/`
`01_matrix.py` zuerst, dann 02 vor 03 (03 liest `basis.npz`), 04–07 in beliebiger Reihenfolge.

### Datenordner für einbrueche/ und rebalancing/

Beide lesen Tageskerzen aus `skripte/daten/historie/` — eine JSON-Datei je Titel:

```json
{"symbol": "XYZ", "bars": [{"bar_date": "2018-01-02", "open": 1.0, "high": 1.0,
  "low": 1.0, "close": 1.0, "volume": 0.0}]}
```

Kurse von yfinance, `auto_adjust=True`, ab 2018-01-01. Vor dem Speichern wurde die
OHLC-Ordnung erzwungen (Low = min(Low, Open, Close), High = max(High, Open, Close)), weil
adjustierte Kurse um Ausschüttungstage herum sonst leicht widersprüchlich sind.

**Ein Ladeskript für diesen Ordner liegt nicht bei:** Der Ladeweg im Projekt holte die
Titelliste aus der Datenbank des laufenden Systems (das Screener-Universum am Messtag)
und nutzte dessen Normalisierungsfunktion. Wer nachmessen will, füllt den Ordner mit
eigenen Titeln im Format oben.

**Datenstand des Befunds:** 633 Titel, 1.240.819 Tageskerzen, 2018-01-02 → 2026-08-28.
Hash über die Dateien (nachgerechnet, im Befund selbst nicht festgehalten):

```bash
cd skripte/daten/historie && sha256sum $(ls *.json | LC_ALL=C sort) | sha256sum
```

`eb00 4350 4d43 9893 71fe 3284 6696 20fa e616 e9ff f00e df63 0525 aa09 fbb7 ae7e`

Alle Titel haben bis zum Messtag überlebt; delistete Titel fehlen (Survivorship).

## Nicht enthalten

Diese Messungen gehören zu den Befunden, laufen aber nur gegen die Datenbank oder den
Code des laufenden Systems. Sie sind deshalb hier nur beschrieben, nicht beigelegt.

| Befund | Methode | Grund |
|---|---|---|
| Lage über der 150-Tage-Linie | Median-Vorwärtsrendite (20/60/120 Handelstage) aller Tageszustände über gegen unter der EMA150, je Kalenderjahr, plus Kontrollgruppe von Titeln ohne Screener-Pass. | Die Tageszustände stammen aus der Zustandsrekonstruktion mit dem Produktionscode des Systems. |
| Linienbruch als Ausstieg | 20-Tage-Rendite ab Bruchtag gegen blinden Einstieg (Mann-Whitney-U), danach Ausstiegsregeln nach Bruchtiefe und Kategorie. | Liest die rekonstruierten Episoden (Produktionscode) und die Kursreihen aus der Datenbank. |
| Rückeroberung der Linie | Episoden mit dem Zustandsautomaten des Systems nachgebaut (96 % der echten Episoden wiedergefunden), Rückeroberung gegen blinden Einstieg; Docht und Volumen je mit eigener Kontrolle. | Braucht den Produktionscode und den Datenbankzugang. |
| Kuratierung gegen Zufall | Perzentil jeder Watchlist-Aufnahme in dem Pool, aus dem sie gewählt wurde, 20 und 60 Handelstage ab Open des Folgetags. | Aufnahmen und Pools liegen nur in der Datenbank; die Watchlist-Titel gehören nicht ins Repo. |
| Faktor-Rotation, Probe | Bitidentitäts-Vergleich des nachgerechneten Signals gegen die täglich gespeicherten Werte des Systems. | Braucht die Datenbank; das Signal selbst rechnet `02_signal.py`. |
