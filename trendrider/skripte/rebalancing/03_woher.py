"""Schritt 3: Woher kommt der Vorteil - und haelt er ohne die Ueberlebenden?

Schritt 2 sagt: Rebalancing schlaegt Buy & Hold, ueber 5 Jahre um +23 Pp. Bevor
das eine Regel wird, zwei Fragen, die den Befund kippen koennten:

A) IST ES REVERSAL ODER STRUKTUR?
   Zwei voellig verschiedene Ursachen mit demselben Vorzeichen:
     - Reversal: Gewinner fallen zurueck, Rebalancing verkauft sie rechtzeitig.
       Das ist eine EIGENSCHAFT DER STICHPROBE - und Ueberlebende reverten
       systematisch (wer faellt, erholt sich; die anderen sind nicht im Datensatz).
     - Diversification Return: rein mathematisch (Jensen). Ein gleichgewichtetes
       Portfolio hat weniger Varianz als der Mittelwert der Einzelvarianzen, und
       weniger Varianz heisst mehr geometrische Rendite. Haengt an NICHTS ausser
       der Streuung - ueberlebt jede Survivorship-Korrektur.
   Trennung: dieselbe Zeit-Permutation fuer ALLE Titel. Das erhaelt die
   Querschnittskorrelation und die Verteilungen, zerstoert aber jede Zeitstruktur
   (Momentum, Reversal, Trend). Was danach uebrigbleibt, ist Struktur.

B) AB WELCHER PLEITE-RATE KIPPT ES?
   Kein erfundener Parameter, sondern eine Grenzaussage: wie viele Totalverluste
   pro Jahr muesste die echte Welt enthalten, damit der Vorteil verschwindet?
   Dann laesst sich das gegen eigene Erfahrung halten.
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
d = np.load(f"{HERE}/basis.npz", allow_pickle=True)
R = d["R"]
KOSTEN = 0.0010
rng = np.random.default_rng(20260914)

def laufe(rr):
    T, n = rr.shape
    bh = np.prod(1 + rr, axis=0).mean()
    port = 1 + rr.mean(axis=1)
    w_nach = (1 + rr) / (n * port[:, None])
    to = np.abs(w_nach - 1.0 / n).sum(axis=1) / 2.0
    return bh, np.prod(port * (1 - to * KOSTEN))

N, DAUER, NT = 4000, 260, 10
print(f"=== A) Reversal oder Struktur? ({NT} Titel, {DAUER} Wochen, {N} Koerbe) ===\n")
for name, permut in (("echte Reihenfolge", False), ("Zeit gemeinsam permutiert", True)):
    diffs, siege = [], 0
    for _ in range(N):
        t0 = rng.integers(0, R.shape[0] - DAUER)
        idx = rng.choice(R.shape[1], size=NT, replace=False)
        rr = R[t0:t0 + DAUER][:, idx]
        if permut:
            rr = rr[rng.permutation(DAUER)]      # GLEICHE Permutation fuer alle Titel
        bh, ew = laufe(rr)
        diffs.append(ew - bh); siege += ew > bh
    diffs = np.array(diffs)
    print(f"    {name:<28} Δ Median {np.median(diffs):+.3f} · "
          f"EW gewinnt {siege/N:.1%} · Δ Mittel {diffs.mean():+.3f}")
print("\n    Bleibt der Vorteil nach der Permutation, ist er Diversification Return")
print("    (strukturell, survivorship-fest). Verschwindet er, war es Reversal der")
print("    Ueberlebenden - und dann traegt der Befund nicht.")

print(f"\n=== B) Ab welcher Totalverlust-Rate kippt der Vorteil? ===")
print(f"    Ein getroffener Titel verliert ueber 8 Wochen 90 % und erholt sich nie.")
print(f"    Buy & Hold traegt ihn mit absteigendem Gewicht, Rebalancing kauft nach.\n")
print(f"    {'p/Jahr':>8} {'erwartet je Korb':>18} {'Δ netto Median':>16} {'EW gewinnt':>12}")
for p_jahr in (0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08):
    diffs, siege = [], 0
    for _ in range(N):
        t0 = rng.integers(0, R.shape[0] - DAUER)
        idx = rng.choice(R.shape[1], size=NT, replace=False)
        rr = R[t0:t0 + DAUER][:, idx].copy()
        # Pleiten einstreuen: je Titel und Jahr mit p, Absturz ueber 8 Wochen
        for j in range(NT):
            for jahr in range(DAUER // 52):
                if rng.random() < p_jahr:
                    s = jahr * 52 + rng.integers(0, 44)
                    rr[s:s + 8, j] = (0.10) ** (1 / 8) - 1     # -90 % ueber 8 Wochen
                    rr[s + 8:, j] = 0.0                        # danach tot
                    break
        bh, ew = laufe(rr)
        diffs.append(ew - bh); siege += ew > bh
    diffs = np.array(diffs)
    print(f"    {p_jahr:>7.1%} {p_jahr*NT*DAUER/52:>18.1f} {np.median(diffs):>+16.3f} {siege/N:>11.1%}")
