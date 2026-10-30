"""Schritt 7: 06 war falsch gebaut - Korrektur.

In 06 waren im Modus "hoechste ADR" nur 3 der 10 Titel ueberhaupt gefaehrdet,
bei unveraenderter Einzelwahrscheinlichkeit. Damit sank die ERWARTETE ZAHL der
Pleiten auf 30 %, und das Ergebnis las sich als "konzentriertes Risiko ist
milder" - gemessen war aber schlicht weniger Risiko.

Fair ist nur, was die erwartete Anzahl konstant haelt und allein verschiebt,
WEN es trifft: p_eff = p * NT / k fuer die k gefaehrdeten Titel.
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
    r_ = np.array([b["high"] / b["low"] for b in bars])
    c = np.cumsum(np.insert(r_, 0, 0.0)); adr = (c[20:] - c[:-20]) / 20.0 - 1.0
    letzte = {}
    for k, a in enumerate(adr):
        y, w, _ = datetime.date.fromisoformat(bars[k + 19]["bar_date"]).isocalendar()
        letzte[f"{y}-{w:02d}"] = a
    for w, a in letzte.items():
        if w in wi: A[wi[w], sj[sym]] = a
P = M[:, voll]; R = P[1:] / P[:-1] - 1.0; Ain = A[:, voll][:-1]
t0s = int(np.argmax(np.isfinite(Ain).all(axis=1))); R, Ain = R[t0s:], Ain[t0s:]

KOSTEN = 0.0010; rng = np.random.default_rng(20260914)
def laufe(rr, ww):
    wert, w_ist = 1.0, ww[0].copy()
    for t in range(rr.shape[0]):
        wert *= (1 - np.abs(ww[t] - w_ist).sum() / 2.0 * KOSTEN)
        w = ww[t]; r = (w * rr[t]).sum(); wert *= (1 + r)
        w_ist = w * (1 + rr[t]) / (1 + r)
    return wert

N, DAUER, NT, K = 1200, 260, 10, 3
print(f"=== Wen trifft die Pleite? Gleiche erwartete Anzahl ({NT} Titel, {N} Koerbe) ===")
print(f"    Modus 'nur die {K} volatilsten': p_eff = p * {NT}/{K} = p * {NT/K:.2f}\n")
print(f"    {'p/Jahr':>7} {'Treffer':>24} {'Pleiten/Korb':>13} {'gleich':>22} {'nach ADR':>22}")
for p_jahr in (0.02, 0.03):
    for modus in ("zufaellig (alle 10)", f"nur die {K} volatilsten"):
        p_eff = p_jahr * (NT / K) if modus.startswith("nur") else p_jahr
        res = {"gleich": [], "nach ADR": []}; bhs = []; n_pl = []
        for _ in range(N):
            t0 = rng.integers(0, R.shape[0] - DAUER)
            idx = rng.choice(R.shape[1], size=NT, replace=False)
            rr = R[t0:t0 + DAUER][:, idx].copy(); aa = Ain[t0:t0 + DAUER][:, idx]
            kand = np.argsort(-aa.mean(axis=0))[:K] if modus.startswith("nur") else range(NT)
            z = 0
            for j in kand:
                for jahr in range(DAUER // 52):
                    if rng.random() < min(p_eff, 1.0):
                        s = jahr * 52 + rng.integers(0, 44)
                        rr[s:s + 8, j] = 0.10 ** (1 / 8) - 1; rr[s + 8:, j] = 0.0
                        z += 1; break
            n_pl.append(z)
            bhs.append(np.prod(1 + rr, axis=0).mean())
            res["gleich"].append(laufe(rr, np.full_like(rr, 1.0 / NT)))
            dv = np.clip(aa, 1e-4, None); res["nach ADR"].append(laufe(rr, dv / dv.sum(1, keepdims=True)))
        bh = np.array(bhs); zl = f"    {p_jahr:>6.1%} {modus:>24} {np.mean(n_pl):>13.2f}"
        for k in ("gleich", "nach ADR"):
            v = np.array(res[k]); zl += f"{np.median(v - bh):>+11.3f}{(v > bh).mean():>11.1%}"
        print(zl)
