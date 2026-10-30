"""Schritt 1b — risikofreier Zins (DGS3MO) aus FRED.

Bewusst eigene Datei mit eigenem Hash: FRED ist eine andere Quelle als yfinance, und
der Panel-Hash aus 01_daten.py soll stabil bleiben, wenn hier nachgeladen wird.

DGS3MO ist eine ANNUALISIERTE Prozentzahl (4.25 = 4,25 %/Jahr). Für tägliche
Cash-Renditen wird linear geteilt (/252) — nicht geometrisch: bei Sätzen dieser
Größenordnung ist der Unterschied < 1 bp/Jahr und die lineare Form ist die Konvention
des übrigen Projekts (`r_f/252`).

Braucht die Umgebungsvariable FRED_API_KEY (kostenloser Schlüssel bei FRED).

    python 01b_riskfree.py [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HIER = Path(__file__).resolve().parent
RF = HIER / "daten" / "riskfree.parquet"
META = HIER / "daten" / "riskfree.meta.json"
SERIE = "DGS3MO"
START = "2013-01-01"


def laden() -> pd.Series:
    import requests

    key = os.getenv("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY fehlt (Umgebungsvariable).")

    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": SERIE, "api_key": key, "file_type": "json",
                             "observation_start": START}, timeout=60)
    r.raise_for_status()
    obs = r.json()["observations"]
    s = pd.Series({pd.Timestamp(o["date"]): (float(o["value"]) if o["value"] != "." else None)
                   for o in obs}, name="dgs3mo_pct")
    # FRED liefert "." an Feiertagen → vorwärtsfüllen (der Satz gilt weiter).
    return s.astype("float64").ffill().dropna()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if RF.exists() and not a.force:
        m = json.loads(META.read_text(encoding="utf-8"))
        print(f"  Bereits vorhanden ({m['erste']} → {m['letzte']}, {m['n']} Werte). "
              f"--force zum Überschreiben.")
        return 0

    s = laden()
    s.to_frame().to_parquet(RF, engine="pyarrow", compression="zstd")
    h = hashlib.sha256(RF.read_bytes()).hexdigest()
    meta = {"erzeugt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "serie": SERIE, "quelle": "FRED", "erste": str(s.index[0].date()),
            "letzte": str(s.index[-1].date()), "n": int(len(s)), "sha256": h,
            "einheit": "Prozent p.a. (annualisiert); taeglich = /252"}
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  {SERIE}: {meta['erste']} → {meta['letzte']}  ({meta['n']} Werte)")
    print(f"  aktuell {s.iloc[-1]:.2f} %  ·  Median {s.median():.2f} %  "
          f"·  Spanne {s.min():.2f}–{s.max():.2f} %")
    print(f"  SHA256: {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
