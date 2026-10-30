"""Zusatz — war die ΔSharpe-Schwelle von 0,40 richtig kalibriert?

Ausgangsfrage (25.07.): „war es nicht so, dass wir erstmal eine festgelegt haben, weil
nichts vorhanden war, um dann später mit Daten zu rekalibrieren?" — **Ja.** Die Vorab-Spezifikation
*behauptet* „bei n_eff ≈ 30 ist eine Sharpe-Differenz unter ~0,40 nicht von Null
unterscheidbar", leitet das aber nicht her, und ihre Prüfliste fragt selbst „richtig kalibriert?".

Die plausible Herleitung ist `1,96/√30 ≈ 0,36 ≈ 0,40` — der Standardfehler eines
**einzelnen** Sharpe Ratio. Gemessen wird hier aber die **Differenz zweier extrem
korrelierter** Sharpes: Strategie und W0 halten dieselben sechs ETFs, nur anders
gewichtet. Bei hoher Korrelation ist der SE der Differenz drastisch kleiner als der SE
eines einzelnen SR — die Schwelle wäre dann **zu streng**.

Dieses Skript misst die Nullverteilung EMPIRISCH: Score-Zuordnung permutieren (wie Schritt 6,
nur ΔSharpe statt IR), alles andere identisch. Das 95-Perzentil dieser Verteilung ist
die datengestützte Schwelle.

⚠️ **Das Urteil dieses Laufs bleibt unberührt.** Vorab festgelegt: „Nachträgliche Absenkung ist
Betrug am eigenen Test. Änderung nur VOR dem ersten Lauf." Dieses Skript beantwortet,
ob die Schwelle für KÜNFTIGE Läufe richtig gesetzt war — es bewertet den vorliegenden
Lauf nicht neu.

    python 08_schwelle.py [--pfade 3000]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

mc = import_module("06_montecarlo")

HIER = Path(__file__).resolve().parent
ERG = HIER / "ergebnisse"


def sharpe_m(r: np.ndarray) -> float:
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(12)) if sd > 0 else np.nan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pfade", type=int, default=3000)
    ap.add_argument("--schema", default="W1k2")
    a = ap.parse_args()

    R, rb = mc.monatspanel()
    S = mc.scores_aus(R, rb)
    strat = mc.fahre_monat(R, S, a.schema)
    w0 = mc.fahre_monat(R, S, "W0")
    beob_d = sharpe_m(strat) - sharpe_m(w0)

    print("=" * 78)
    print("  WAR DIE SCHWELLE 0,40 RICHTIG KALIBRIERT?")
    print("=" * 78)
    print(f"    Schema {a.schema} · {len(strat)} Monate")
    print(f"    Korrelation Strategie ↔ W0:  {np.corrcoef(strat, w0)[0,1]:.4f}")
    print(f"      → Genau hier liegt der Kern: die 0,40 stammt (plausibel) aus dem SE")
    print(f"        eines EINZELNEN Sharpe (1,96/√30 ≈ 0,36). Bei dieser Korrelation ist")
    print(f"        der SE der DIFFERENZ aber ein Bruchteil davon.")
    print(f"\n    beobachtete ΔSharpe: {beob_d:+.4f}")

    # --- Nullverteilung: Score bedeutungslos, alles andere identisch (wie Schritt 6) ---
    rng = np.random.default_rng(2026)
    null = np.empty(a.pfade)
    for p in range(a.pfade):
        Sp = S.copy()
        for t in range(len(Sp)):
            if np.isfinite(Sp[t]).any():
                Sp[t] = Sp[t][rng.permutation(Sp.shape[1])]
        null[p] = sharpe_m(mc.fahre_monat(R, Sp, a.schema)) - sharpe_m(w0)
    null = null[np.isfinite(null)]

    se = float(null.std(ddof=1))
    p95, p99 = np.percentile(null, [95, 99])
    p_wert = float((null >= beob_d).mean())

    print(f"\n  Nullverteilung der ΔSharpe ({len(null)} Permutationen):")
    print(f"    Mittel {null.mean():+.4f}   SE {se:.4f}")
    print(f"    95-Perzentil {p95:+.4f}   99-Perzentil {p99:+.4f}")
    print(f"\n  ⇒ **Datengestützte Schwelle (α = 5 %): ΔSharpe ≥ {p95:.3f}**")
    print(f"     gesetzt war: 0,400   —   Faktor {0.40/p95:.1f}× zu streng"
          if p95 > 0 else "")
    print(f"\n    p-Wert der beobachteten ΔSharpe: {p_wert:.4f}")

    print("\n" + "-" * 78)
    print("  EINORDNUNG — und was NICHT daraus folgt")
    print("-" * 78)
    if beob_d >= p95:
        print(f"    Gegen die GEMESSENE Schwelle wäre {beob_d:+.3f} signifikant (p = {p_wert:.4f}).")
    else:
        print(f"    Auch gegen die gemessene Schwelle bleibt {beob_d:+.3f} nicht signifikant.")
    print("    ABER: Das Urteil des Laufs vom 25.07. bleibt „keine Evidenz\" (vorab festgelegt —")
    print("    nachträgliche Absenkung ist Betrug am eigenen Test). Diese Messung gilt")
    print("    für KÜNFTIGE Läufe und muss VOR dem nächsten Lauf in die Vorab-Spezifikation.")
    print("\n    Und sie ersetzt die DSR/PBO-Befunde nicht: dass eine einzelne Variante")
    print("    signifikant aussieht, ändert nichts daran, dass 42 getestet wurden")
    print("    (DSR 0 von 36) und die Auswahl nicht funktioniert (PBO 0,642).")

    np.savez(ERG / "schwelle.npz", null=null, beob=beob_d, p95=p95, se=se)
    print(f"\n  → ergebnisse/schwelle.npz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
