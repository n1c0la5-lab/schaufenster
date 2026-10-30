"""Schritt 1 — Datenbeschaffung + Einfrieren.

Zieht die sechs Faktor-ETFs + SPY einmal, friert sie als Parquet ein und hasht sie.

WARUM EINFRIEREN: yfinance rechnet Ausschüttungen RÜCKWÄRTS in die Reihe.
Ein Lauf heute und einer in sechs Monaten liefern andere Zahlen — ohne eingefrorene
Rohdaten ist jedes Ergebnis ein Einzelstück, das niemand (auch wir nicht) reproduzieren
kann. Der Hash steht im Experiment-Log; jede spätere Kennzahl verweist darauf.

Gezogen wird `auto_adjust=True` (Total-Return: Splits UND Ausschüttungen rückgerechnet).
Das ist für einen Allokations-Backtest die richtige Wahl — wir vergleichen Anlagen, die
man tatsächlich gehalten hätte, inklusive reinvestierter Ausschüttungen.

    python 01_daten.py            # ziehen + einfrieren (bricht ab, wenn schon vorhanden)
    python 01_daten.py --force    # überschreiben (neuer Hash, neues Experiment!)
    python 01_daten.py --verify   # nur prüfen: stimmt der Hash der vorhandenen Datei?
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

HIER = Path(__file__).resolve().parent
DATEN = HIER / "daten"
PANEL = DATEN / "faktor_panel.parquet"
META = DATEN / "faktor_panel.meta.json"

# Sechs Faktoren + Benchmark. IWF gegen SPY (Nenner-Konsistenz ⚠️),
# SIZE mit (Entscheidung 2026-07-25). Auflagedaten am 25.07. gegen den Feed gemessen.
TICKER = ["VLUE", "QUAL", "MTUM", "IWF", "USMV", "SIZE", "SPY"]
AUFLAGE = {  # hart fixiert — Gewicht vor diesem Datum = 0, nicht NaN-Füllung
    "VLUE": "2013-04-01", "QUAL": "2013-07-01", "MTUM": "2013-04-01",
    "IWF": "2000-05-01", "USMV": "2011-10-01", "SIZE": "2013-04-01", "SPY": "1993-01-01",
}
START = "2013-01-01"          # vor dem spätesten Listing, damit der Anlauf sichtbar ist


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def laden() -> pd.DataFrame:
    """Adjusted Close + Open je Ticker, als flaches Panel (Datum × Feld×Ticker)."""
    roh = yf.download(TICKER, start=START, interval="1d", group_by="ticker",
                      auto_adjust=True, progress=False, threads=True)
    if roh.empty:
        raise RuntimeError("yfinance lieferte ein leeres Panel.")

    teile = {}
    for t in TICKER:
        df = roh[t] if isinstance(roh.columns, pd.MultiIndex) else roh
        teile[("close", t)] = df["Close"]
        teile[("open", t)] = df["Open"]
    panel = pd.DataFrame(teile)
    panel.columns = pd.MultiIndex.from_tuples(panel.columns, names=["feld", "ticker"])
    panel.index.name = "datum"

    # Randtag-Prüfung wie im laufenden Kurs-Feed: steht ein Tag
    # im Index, hat aber bei KEINEM Ticker einen Close, ist die Feed-Antwort defekt.
    # Für einen Monats-Backtest ist ein fehlender Randtag harmlos — er darf nur nicht
    # unbemerkt in die Datei wandern.
    letzte = panel["close"].iloc[-1]
    if letzte.isna().all():
        print(f"  ⚠️  Randtag {panel.index[-1].date()} ohne jeden Close — wird verworfen "
              f"(bekannter Yahoo-Defekt).")
        panel = panel.iloc[:-1]

    return panel.dropna(how="all")


def einfrieren(panel: pd.DataFrame) -> dict:
    DATEN.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(PANEL, engine="pyarrow", compression="zstd")
    meta = {
        "erzeugt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ticker": TICKER,
        "auflage": AUFLAGE,
        "quelle": "yfinance, auto_adjust=True (Total-Return)",
        "start": START,
        "erste_zeile": str(panel.index[0].date()),
        "letzte_zeile": str(panel.index[-1].date()),
        "handelstage": int(len(panel)),
        "sha256": _sha256(PANEL),
        "hinweis": ("Retro-Adjustment: yfinance rechnet Ausschuettungen rueckwaerts. "
                    "Diese Datei ist die eingefrorene Referenz; jedes Ergebnis verweist auf den Hash."),
    }
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def bericht(panel: pd.DataFrame, meta: dict) -> None:
    print(f"\n  Panel: {meta['erste_zeile']} → {meta['letzte_zeile']}  "
          f"({meta['handelstage']} Handelstage)")
    print(f"  SHA256: {meta['sha256']}")
    print("\n  Erste verfügbare Zeile je Ticker (Gegenprobe zu AUFLAGE):")
    close = panel["close"]
    for t in TICKER:
        erste = close[t].first_valid_index()
        soll = AUFLAGE[t]
        # Ein ETF, der VOR dem Panel-Start (START) aufgelegt wurde, beginnt zwangsläufig
        # am Panel-Start — das ist kein Defekt. Verglichen wird deshalb gegen
        # max(Auflage, START), nicht gegen die Auflage allein.
        erwartet = max(soll, START)
        ok = "✓" if erste is not None and str(erste.date())[:7] <= erwartet[:7] else "⚠"
        alt = " (älter als Panel-Start)" if soll < START else ""
        print(f"    {ok} {t:5} {str(erste.date()) if erste is not None else '—':12} "
              f"(fixiert: {soll}{alt})")

    gemeinsam = close.dropna().index
    print(f"\n  Gemeinsame Historie (alle {len(TICKER)} Reihen vollständig): "
          f"{gemeinsam[0].date()} → {gemeinsam[-1].date()}  ({len(gemeinsam)} HT)")
    monate = pd.Series(gemeinsam).dt.to_period("M").nunique()
    print(f"  Monats-Rebalances daraus : ~{monate - 12} "
          f"nach 252-HT-z-Score-Vorlauf")


def main() -> int:
    ap = argparse.ArgumentParser(description="Schritt 1 — Daten einfrieren")
    ap.add_argument("--force", action="store_true", help="vorhandene Datei überschreiben")
    ap.add_argument("--verify", action="store_true", help="nur Hash der vorhandenen Datei prüfen")
    a = ap.parse_args()

    if a.verify:
        if not PANEL.exists() or not META.exists():
            print("  ✗ Keine eingefrorene Datei vorhanden.")
            return 1
        meta = json.loads(META.read_text(encoding="utf-8"))
        ist = _sha256(PANEL)
        ok = ist == meta["sha256"]
        print(f"  {'✓' if ok else '✗'} Hash {'stimmt' if ok else 'WEICHT AB'}")
        if not ok:
            print(f"    soll {meta['sha256']}\n    ist  {ist}")
        return 0 if ok else 1

    if PANEL.exists() and not a.force:
        meta = json.loads(META.read_text(encoding="utf-8"))
        print(f"  Bereits eingefroren ({meta['erste_zeile']} → {meta['letzte_zeile']}). "
              f"--force zum Überschreiben.")
        print(f"  SHA256: {meta['sha256']}")
        return 0

    print(f"  Lade {len(TICKER)} Ticker ab {START} …")
    panel = laden()
    meta = einfrieren(panel)
    bericht(panel, meta)
    print(f"\n  → {PANEL.relative_to(HIER)}  +  {META.relative_to(HIER)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
