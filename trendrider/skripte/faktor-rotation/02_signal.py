"""Schritt 2 — Signal-Engine (RRG-Kern).

Rechnet den RRG-Kern auf dem eingefrorenen Panel nach — **wortgleich zum Rechenkern
des laufenden Systems**, nicht "sinngemäß". Der Score benutzt ausschließlich die
Ratio-Achse:

    RS_i(t)       = Close_i(t) / Close_SPY(t)
    rs_ratio_i(t) = 100 + zscore(RS_i, W1=252, min_hist=130)
    rs_mom_i(t)   = 100 + zscore(ROC(rs_ratio_i, W2=50), W1=252, min_hist=130)   [nur S2]
    S_i(t)        = rs_ratio_i(t) − 100

Im ursprünglichen Aufbau lief danach eine Bitidentitäts-Probe gegen die Werte, die das
laufende System täglich speichert (Toleranz 1e-4 = Rundung der gespeicherten Spalte):
Stimmt die Nachrechnung nicht, rechnet der Backtest etwas anderes als das System, und
jedes spätere Ergebnis wäre eine Aussage über den Nachbau, nicht über die Strategie.
Die Probe braucht die Datenbank des Systems und ist hier nicht enthalten.

    python 02_signal.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HIER = Path(__file__).resolve().parent
PANEL = HIER / "daten" / "faktor_panel.parquet"
SIGNAL = HIER / "daten" / "signal.parquet"

# Unverändert aus dem laufenden System übernommen — hier neu zu kalibrieren hieße,
# an den Testdaten nachzujustieren.
W1, W2, MIN_HIST = 252, 50, 130
BENCH = "SPY"
FAKTOREN = ["VLUE", "QUAL", "MTUM", "IWF", "USMV", "SIZE"]


def _z(s: pd.Series, win: int, min_hist: int) -> pd.Series:
    """z-Score wie im laufenden System — inkl. σ=0 → NaN statt Division durch Null."""
    mu = s.rolling(win, min_periods=min_hist).mean()
    sd = s.rolling(win, min_periods=min_hist).std(ddof=1)
    return (s - mu) / sd.replace(0, np.nan)


def rechne(panel: pd.DataFrame) -> pd.DataFrame:
    """{ratio, mom} je Faktor über die volle Historie."""
    close = panel["close"]
    out: dict[tuple[str, str], pd.Series] = {}
    for f in FAKTOREN:
        # align(join="inner") — nur gemeinsame Handelstage.
        a, b = close[f].align(close[BENCH], join="inner")
        a, b = a.dropna(), b.reindex(a.dropna().index)
        rs = (a / b).dropna()
        ratio = 100 + _z(rs, W1, MIN_HIST)
        mom = 100 + _z(ratio.pct_change(W2), W1, MIN_HIST)
        out[("ratio", f)] = ratio
        out[("mom", f)] = mom
    df = pd.DataFrame(out)
    df.columns = pd.MultiIndex.from_tuples(df.columns, names=["feld", "faktor"])
    df.index.name = "datum"
    return df


def main() -> int:
    ap = argparse.ArgumentParser(description="Schritt 2 — Signal")
    ap.parse_args()

    if not PANEL.exists():
        print("  ✗ Kein eingefrorenes Panel — erst 01_daten.py laufen lassen.")
        return 1

    panel = pd.read_parquet(PANEL)
    sig = rechne(panel)
    sig.to_parquet(SIGNAL, engine="pyarrow", compression="zstd")

    gueltig = sig["ratio"].dropna(how="all")
    print(f"  Signal: {gueltig.index[0].date()} → {gueltig.index[-1].date()}  "
          f"({len(gueltig)} Handelstage mit mindestens einem Score)")
    voll = sig["ratio"].dropna()
    print(f"  Alle {len(FAKTOREN)} Faktoren gleichzeitig gültig ab: {voll.index[0].date()}"
          f"  ({len(voll)} HT)")
    print(f"  → {SIGNAL.relative_to(HIER)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
