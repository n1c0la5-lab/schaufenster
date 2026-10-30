"""Schritt 5: Der Kipppunkt je Gewichtung - besonders fuer "nach ADR".

Schritt 4 sagt: "nach ADR gewichten" schlaegt alles (+0,345 gegen B&H). Das ist
erwartbar, wenn der Vorteil Diversification Return ist - der waechst mit der
Einzelvolatilitaet. Aber genau diese Variante laedt am meisten von der Sorte
Titel ins Buch, die -90 % machen kann, UND kauft sie im Absturz nach.

Einen Befund zu melden, dessen Hauptrisiko nicht gemessen ist, waere hier der
teuerste Fehler. Also derselbe Pleite-Test wie in 03, aber je Gewichtung.
"""
import json, glob, os, datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "..", "daten", "historie")
d = np.load(f"{HERE}/wochen.npz", allow_pickle=True)
M, syms, wochen = d["M"], d["syms"], d["wochen"]
voll = np.isfinite(M).all(axis=0); S_voll = set(syms[voll].tolist())
wi = {w: i for i, w in enumerate(wochen)}; sj = {s: j for j, s in enumerate(syms)}
A = np.full((len(wochen), len(syms)), np.nan)
for f in sorted(glob.glob(f"{HIST}/*.json")):
    dd = json.load(open(f)); sym = dd["symbol"]
    if sym not in S_voll: continue
    bars = [b for b in dd["bars"] if b.get("high") and b.get("low") and b["low"] > 0]
    if len(bars) < 25: continue
    rng_ = np.array([b["high"] / b["low"] for b in bars])
    c = np.cumsum(np.insert(rng_, 0, 0.0)); adr = (c[20:] - c[:-20]) / 20.0 - 1.0
    letzte = {}
    for k, a in enumerate(adr):
        y, w, _ = datetime.date.fromisoformat(bars[k + 19]["bar_date"]).isocalendar()
        letzte[f"{y}-{w:02d}"] = a
    for w, a in letzte.items():
        if w in wi: A[wi[w], sj[sym]] = a
P = M[:, voll]; R = P[1:] / P[:-1] - 1.0; Ain = A[:, voll][:-1]
t0s = int(np.argmax(np.isfinite(Ain).all(axis=1))); R, Ain = R[t0s:], Ain[t0s:]

KOSTEN = 0.0010
rng = np.random.default_rng(20260914)
def laufe(rr, ww):
    wert, w_ist = 1.0, ww[0].copy()
    for t in range(rr.shape[0]):
        wert *= (1 - np.abs(ww[t] - w_ist).sum() / 2.0 * KOSTEN)
        w = ww[t]; r = (w * rr[t]).sum(); wert *= (1 + r)
        w_ist = w * (1 + rr[t]) / (1 + r)
    return wert

N, DAUER, NT = 2500, 260, 10
print(f"=== Kipppunkt je Gewichtung ({NT} Titel, {DAUER} Wochen, {N} Koerbe) ===")
print("    Ein getroffener Titel: -90 % ueber 8 Wochen, danach tot.\n")
print(f"    {'p/Jahr':>7} " + "".join(f"{k:>26}" for k in ("gleich", "nach ADR")))
print(f"    {'':>7} " + "".join(f"{'Δ vs B&H':>13}{'gewinnt':>13}" for _ in range(2)))
for p_jahr in (0.0, 0.005, 0.01, 0.02, 0.03, 0.05):
    res = {"gleich": [], "nach ADR": []}; bhs = []
    for _ in range(N):
        t0 = rng.integers(0, R.shape[0] - DAUER)
        idx = rng.choice(R.shape[1], size=NT, replace=False)
        rr = R[t0:t0 + DAUER][:, idx].copy(); aa = Ain[t0:t0 + DAUER][:, idx]
        for j in range(NT):
            for jahr in range(DAUER // 52):
                if rng.random() < p_jahr:
                    s = jahr * 52 + rng.integers(0, 44)
                    rr[s:s + 8, j] = 0.10 ** (1 / 8) - 1; rr[s + 8:, j] = 0.0
                    break
        bhs.append(np.prod(1 + rr, axis=0).mean())
        res["gleich"].append(laufe(rr, np.full_like(rr, 1.0 / NT)))
        dv = np.clip(aa, 1e-4, None); res["nach ADR"].append(laufe(rr, dv / dv.sum(1, keepdims=True)))
    bh = np.array(bhs)
    zeile = f"    {p_jahr:>6.1%} "
    for k in ("gleich", "nach ADR"):
        v = np.array(res[k]); zeile += f"{np.median(v - bh):>+13.3f}{(v > bh).mean():>13.1%}"
    print(zeile)
