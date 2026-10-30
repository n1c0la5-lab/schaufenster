"""Schritt 1: Wochen-Kursmatrix aus der vorhandenen Historie (633 Symbole ab 2018).

Quelle: ../daten/historie/ (Format in skripte/README.md) - dieselben adjustierten
Kurse wie die Messung zur 150-Tage-Linie. Kein neuer Download.

Wochenschluss = letzter Handelstag je ISO-Woche. Bewusst NICHT "jeden Freitag":
Feiertagswochen haetten sonst Luecken, und eine Luecke im Rebalance-Kalender
verschiebt Gewichte, ohne dass es auffaellt.
"""
import json, glob, os, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "..", "daten", "historie")

reihen, alle_wochen = {}, set()
for f in sorted(glob.glob(f"{HIST}/*.json")):
    d = json.load(open(f))
    sym, bars = d["symbol"], d["bars"]
    if not bars: continue
    wo = {}                                  # ISO-Woche -> (datum, close)
    for b in bars:
        c = b.get("close")
        if c is None or not np.isfinite(c) or c <= 0: continue
        y, w, _ = __import__("datetime").date.fromisoformat(b["bar_date"]).isocalendar()
        k = f"{y}-{w:02d}"
        if k not in wo or b["bar_date"] > wo[k][0]: wo[k] = (b["bar_date"], float(c))
    if len(wo) >= 60:
        reihen[sym] = {k: v[1] for k, v in wo.items()}
        alle_wochen |= set(wo)

wochen = sorted(alle_wochen)
syms = sorted(reihen)
print(f"Symbole: {len(syms)} · Wochen: {len(wochen)} ({wochen[0]} … {wochen[-1]})")

M = np.full((len(wochen), len(syms)), np.nan)
wi = {w: i for i, w in enumerate(wochen)}
for j, s in enumerate(syms):
    for w, c in reihen[s].items(): M[wi[w], j] = c

voll = np.isfinite(M).all(axis=0)
print(f"Ueber den ganzen Zeitraum lueckenlos: {voll.sum()} von {len(syms)}")
print(f"Abdeckung je Woche: min {np.isfinite(M).sum(axis=1).min()}, "
      f"max {np.isfinite(M).sum(axis=1).max()}")

np.savez_compressed(f"{HERE}/wochen.npz", M=M, syms=np.array(syms), wochen=np.array(wochen))
print(f"→ {HERE}/wochen.npz")
