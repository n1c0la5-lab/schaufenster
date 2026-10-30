"""Schritt 2: Variante 1 der Ausgangsfrage - woechentlich zurueck auf Gleichgewicht.

Die Frage in einem Satz: Wenn ein Titel auf 15 % laeuft und ich ihn jede Woche
auf 10 % zurueckschneide - verdiene ich damit Geld oder verschenke ich welches?

Beides ist moeglich und haengt an EINER Eigenschaft der Titel:
  - laufen Gewinner weiter (Momentum), schneidet Rebalancing sie ab  -> es kostet
  - fallen Gewinner zurueck (Reversal), verkauft es teuer und kauft billig -> es verdient

Kontrollmass ist Buy & Hold aus demselben Korb, demselben Startdatum, denselben
Startgewichten. Ohne das misst man den Zeitraum, nicht die Regel.

Kosten: Round-Trip 0,10 % auf den UMGESETZTEN Turnover (wie in ../faktor-rotation/).
Buy & Hold zahlt nach dem Einstieg nichts mehr - das ist der ehrliche Vergleich.

⚠️ SURVIVORSHIP: alle Symbole hier haben 8,7 Jahre ueberlebt. Das verzerrt
ZUGUNSTEN von Rebalancing (ein Absturz, der sich nie erholt, fehlt in der
Stichprobe - genau den wuerde Nachkaufen bestrafen). 03_woher.py (B) misst, wie stark.
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
d = np.load(f"{HERE}/wochen.npz", allow_pickle=True)
M, syms, wochen = d["M"], d["syms"], d["wochen"]
voll = np.isfinite(M).all(axis=0)
P = M[:, voll]                      # lueckenlose Kurse
S = syms[voll]
R = P[1:] / P[:-1] - 1.0            # Wochenrenditen
print(f"Basis: {P.shape[1]} Symbole, {R.shape[0]} Wochenrenditen "
      f"({wochen[0]} … {wochen[-1]})")

KOSTEN = 0.0010                     # Round-Trip auf umgesetzten Turnover
rng = np.random.default_rng(20260914)

def laufe(rr):
    """rr: (T, n) Wochenrenditen. Gibt (BH, EW_ohne, EW_mit, Turnover/Woche)."""
    T, n = rr.shape
    # Buy & Hold: gleichgewichtet gestartet, dann laufen lassen
    bh = np.prod(1 + rr, axis=0).mean()
    # Equal-Weight rebalanciert: Wochenrendite = Mittel der Einzelrenditen
    port = 1 + rr.mean(axis=1)
    ew_ohne = np.prod(port)
    # Turnover: Gewichtsdrift nach jeder Woche, zurueckgeschnitten
    w_nach = (1 + rr) / (n * (1 + rr.mean(axis=1))[:, None])
    to = np.abs(w_nach - 1.0 / n).sum(axis=1) / 2.0
    ew_mit = np.prod(port * (1 - to * KOSTEN))
    return bh, ew_ohne, ew_mit, to.mean()

print(f"\n=== Gleichgewichts-Rebalancing vs. Buy & Hold ===")
print(f"    5000 zufaellige Koerbe je Zelle · Median-Endwert · Kosten {KOSTEN*100:.2f} % Round-Trip")
print(f"\n    {'Titel':>6} {'Dauer':>8} {'B&H':>8} {'EW roh':>8} {'EW netto':>9} "
      f"{'Δ netto':>9} {'EW schlaegt B&H':>16} {'Turnover/Wo':>12}")
N = 5000
T_max = R.shape[0]
for n_titel in (10, 20):
    for dauer in (26, 52, 104, 260):
        bhs, ews, ewm, tos = [], [], [], []
        for _ in range(N):
            t0 = rng.integers(0, T_max - dauer)
            idx = rng.choice(P.shape[1], size=n_titel, replace=False)
            a, b, c, t = laufe(R[t0:t0 + dauer][:, idx])
            bhs.append(a); ews.append(b); ewm.append(c); tos.append(t)
        bhs, ews, ewm = np.array(bhs), np.array(ews), np.array(ewm)
        gewinn = (ewm > bhs).mean()
        print(f"    {n_titel:>6} {dauer:>6} Wo {np.median(bhs):>8.3f} {np.median(ews):>8.3f} "
              f"{np.median(ewm):>9.3f} {np.median(ewm - bhs):>+9.3f} {gewinn:>15.1%} "
              f"{np.mean(tos):>11.2%}")

np.savez_compressed(f"{HERE}/basis.npz", R=R, S=S)
print(f"\n    (Δ netto = Median der Differenz je Korb, nicht Differenz der Mediane.)")
