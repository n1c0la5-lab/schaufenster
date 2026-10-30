"""Die Basisrate: wie viele EMA150-Brueche fuehren ueberhaupt in einen Einbruch?

01 zeigt: fast jeder schwere Einbruch hat einen EMA150-Bruch davor (99 %). Das
klingt nach einem brauchbaren Warnsignal - ist aber die Frage von hinten gelesen.
Entscheidend ist die Gegenrichtung: Von ALLEN Bruechen, wie viele werden schlimm?

Ohne diese Zahl haelt man ein Signal fuer nuetzlich, das fast nur Fehlalarm ist.
"""
import json, glob, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "..", "daten", "historie")
HOCH_N, EMA_N = 252, 150

def ema(x, n):
    a = 2.0 / (n + 1.0); out = np.empty_like(x); out[0] = x[0]
    for i in range(1, len(x)): out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out

n_brueche = 0; n_folgt_60 = 0; n_folgt_40 = 0; n_titel = 0
for f in sorted(glob.glob(f"{HIST}/*.json")):
    d = json.load(open(f))
    bars = [b for b in d["bars"] if b.get("close") and b["close"] > 0]
    if len(bars) < 400: continue
    n_titel += 1
    c = np.array([b["close"] for b in bars]); e = ema(c, EMA_N)
    hoch = np.array([c[max(0, i - HOCH_N):i + 1].max() for i in range(len(c))])
    for k in range(EMA_N + 1, len(c) - 1):
        if c[k] < e[k] and c[k - 1] >= e[k - 1]:
            n_brueche += 1
            # laeuft es in den naechsten 252 HT auf -60 % bzw. -40 % vom Hoch?
            fenster = c[k:k + 252] / hoch[k]
            if len(fenster) and fenster.min() - 1.0 <= -0.60: n_folgt_60 += 1
            if len(fenster) and fenster.min() - 1.0 <= -0.40: n_folgt_40 += 1

print(f"Titel: {n_titel}")
print(f"EMA150-Brueche gesamt: {n_brueche}")
print(f"\n  davon binnen 252 HT auf <= -40 % vom Hoch: {n_folgt_40} = {n_folgt_40/n_brueche:.1%}")
print(f"  davon binnen 252 HT auf <= -60 % vom Hoch: {n_folgt_60} = {n_folgt_60/n_brueche:.1%}")
print(f"\n  → Fehlalarmquote fuer '-60 %': {1-n_folgt_60/n_brueche:.1%}")
