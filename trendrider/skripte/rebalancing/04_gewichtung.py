"""Schritt 4: Variante 3 der Ausgangsfrage - nach ADR gewichten statt gleich.

ADR wie im laufenden System: mean(high/low) - 1 ueber 20 Tage, abgelesen
am jeweiligen Wochenschluss. Nur Vergangenheit - der Wert vom Freitag gewichtet
die FOLGENDE Woche, nie die laufende (sonst Blick in die Zukunft).

Drei Gewichtungen im selben Rahmen:
  gleich          w_i = 1/n                     (Variante 1)
  invers ADR      w_i ~ 1/ADR_i                 ruhige Titel groesser
  nach ADR        w_i ~ ADR_i                   volatile Titel groesser

Kontrollmass bleibt Buy & Hold. Kosten wie in 02.
"""
import json, glob, os, datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "..", "daten", "historie")
d = np.load(f"{HERE}/wochen.npz", allow_pickle=True)
M, syms, wochen = d["M"], d["syms"], d["wochen"]
voll = np.isfinite(M).all(axis=0)
S_voll = set(syms[voll].tolist())
wi = {w: i for i, w in enumerate(wochen)}

# --- ADR20 je Symbol am Wochenschluss ---
A = np.full((len(wochen), len(syms)), np.nan)
sj = {s: j for j, s in enumerate(syms)}
for f in sorted(glob.glob(f"{HIST}/*.json")):
    dd = json.load(open(f)); sym = dd["symbol"]
    if sym not in S_voll: continue
    bars = [b for b in dd["bars"]
            if b.get("high") and b.get("low") and b["low"] > 0]
    if len(bars) < 25: continue
    rng_ = np.array([b["high"] / b["low"] for b in bars])
    # rollierendes 20-Tage-Mittel, Wert gilt AB diesem Tag
    c = np.cumsum(np.insert(rng_, 0, 0.0))
    adr = (c[20:] - c[:-20]) / 20.0 - 1.0          # adr[k] gehoert zu bars[k+19]
    letzte = {}
    for k, a in enumerate(adr):
        b = bars[k + 19]
        y, w, _ = datetime.date.fromisoformat(b["bar_date"]).isocalendar()
        letzte[f"{y}-{w:02d}"] = a                  # letzter Tag der Woche gewinnt
    for w, a in letzte.items():
        if w in wi: A[wi[w], sj[sym]] = a

P = M[:, voll]; Aw = A[:, voll]
R = P[1:] / P[:-1] - 1.0
Ain = Aw[:-1]                                       # ADR am Freitag VOR der Woche
ok = np.isfinite(Ain).all(axis=1)
print(f"Basis: {P.shape[1]} Symbole · {R.shape[0]} Wochen · ADR vollstaendig in {ok.sum()}")
t_start = int(np.argmax(ok))                        # ab hier ADR fuer alle da
R, Ain = R[t_start:], Ain[t_start:]
print(f"Auswertungsfenster ab Woche {wochen[t_start+1]} · {R.shape[0]} Wochen")
print(f"ADR-Spanne: {np.nanpercentile(Ain,5):.3f} … {np.nanpercentile(Ain,95):.3f} "
      f"(Median {np.nanmedian(Ain):.3f})")

KOSTEN = 0.0010
rng = np.random.default_rng(20260914)

def laufe(rr, ww):
    """ww: (T,n) Zielgewichte je Woche (Zeile summiert 1). Gibt Endwert netto."""
    wert, w_ist = 1.0, ww[0].copy()
    for t in range(rr.shape[0]):
        to = np.abs(ww[t] - w_ist).sum() / 2.0
        wert *= (1 - to * KOSTEN)
        w = ww[t]
        r = (w * rr[t]).sum()
        wert *= (1 + r)
        w_ist = w * (1 + rr[t]) / (1 + r)
    return wert

N, DAUER, NT = 4000, 260, 10
print(f"\n=== Gewichtung im Vergleich ({NT} Titel, {DAUER} Wochen, {N} Koerbe) ===")
print(f"    {'Variante':<20} {'Endwert Median':>16} {'vs. B&H':>10} {'schlaegt B&H':>14}")
erg = {k: [] for k in ("B&H", "gleich", "invers ADR", "nach ADR")}
for _ in range(N):
    t0 = rng.integers(0, R.shape[0] - DAUER)
    idx = rng.choice(R.shape[1], size=NT, replace=False)
    rr = R[t0:t0 + DAUER][:, idx]; aa = Ain[t0:t0 + DAUER][:, idx]
    erg["B&H"].append(np.prod(1 + rr, axis=0).mean())
    erg["gleich"].append(laufe(rr, np.full_like(rr, 1.0 / NT)))
    iv = 1.0 / np.clip(aa, 1e-4, None); erg["invers ADR"].append(laufe(rr, iv / iv.sum(1, keepdims=True)))
    dv = np.clip(aa, 1e-4, None);       erg["nach ADR"].append(laufe(rr, dv / dv.sum(1, keepdims=True)))
bh = np.array(erg["B&H"])
for k in ("B&H", "gleich", "invers ADR", "nach ADR"):
    v = np.array(erg[k])
    if k == "B&H": print(f"    {k:<20} {np.median(v):>16.3f} {'—':>10} {'—':>14}")
    else: print(f"    {k:<20} {np.median(v):>16.3f} {np.median(v-bh):>+10.3f} {(v>bh).mean():>13.1%}")
