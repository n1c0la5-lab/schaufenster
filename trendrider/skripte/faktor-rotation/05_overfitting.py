"""Schritt 5 — Deflated Sharpe Ratio + PBO via CSCV.

„Bei 42 Konfigurationen auf n_eff ≈ 30 sind sie der Unterschied zwischen einer Messung
und einer Erzählung." (aus der Vorab-Spezifikation)

**DSR** (Bailey/López de Prado 2014) korrigiert den beobachteten Sharpe um den Vorteil,
den man sich durch Mehrfach-Testen erkauft hat. Eingaben: beobachteter SR, Trials N,
Skew und Kurtosis der Renditen, Sample-Länge. Ausgabe: P(wahrer SR > 0) NACH Abzug des
Multiple-Testing-Vorteils.

**PBO via CSCV** beantwortet die andere Frage: Nicht „ist dieser Sieger echt?", sondern
**„taugt die Auswahlprozedur überhaupt?"**. Das Sample wird in S Blöcke zerlegt, über
alle Hälftungen wird die in-sample beste Konfiguration gewählt und ihr out-of-sample
Rang gemessen. PBO > 0,5 heißt: die Prozedur wählt systematisch Verlierer — unabhängig
davon, wie gut der Sieger aussieht.

    python 05_overfitting.py
"""
from __future__ import annotations

import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HIER = Path(__file__).resolve().parent
ERG = HIER / "ergebnisse"
RET = ERG / "tagesrenditen.parquet"

S_BLOECKE = 16
EULER = 0.5772156649


def sharpe(r: pd.Series) -> float:
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(252)) if sd > 0 else np.nan


def dsr(r: pd.Series, n_trials: int, alle_sr: np.ndarray) -> dict:
    """Deflated Sharpe Ratio. `alle_sr` = SR-Verteilung über die getesteten Varianten."""
    r = r.dropna()
    T = len(r)
    sr = sharpe(r) / np.sqrt(252)                    # auf Periodenbasis (täglich)
    g3 = float(stats.skew(r))
    g4 = float(stats.kurtosis(r, fisher=False))

    # Erwarteter Maximal-SR unter der Null (Bailey/LdP Gl. 5)
    var_sr = float(np.var(alle_sr / np.sqrt(252), ddof=1)) if len(alle_sr) > 1 else 0.0
    if var_sr <= 0 or n_trials < 2:
        sr0 = 0.0
    else:
        z1 = stats.norm.ppf(1 - 1.0 / n_trials)
        z2 = stats.norm.ppf(1 - 1.0 / (n_trials * math.e))
        sr0 = math.sqrt(var_sr) * ((1 - EULER) * z1 + EULER * z2)

    nenner = math.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr**2))
    z = (sr - sr0) * math.sqrt(T - 1) / nenner
    return {"sr_ann": sr * np.sqrt(252), "sr0_ann": sr0 * np.sqrt(252),
            "skew": g3, "kurtosis": g4, "dsr": float(stats.norm.cdf(z))}


def pbo_cscv(rets: pd.DataFrame, s: int = S_BLOECKE, max_splits: int = 4000) -> dict:
    """PBO nach Bailey et al. — Anteil der Aufteilungen, in denen die IS-beste
    Konfiguration OOS unter dem Median landet."""
    n = len(rets)
    grenzen = np.linspace(0, n, s + 1, dtype=int)
    bloecke = [rets.iloc[grenzen[i]:grenzen[i + 1]] for i in range(s)]

    alle = list(combinations(range(s), s // 2))
    rng = np.random.default_rng(42)
    if len(alle) > max_splits:                        # C(16,8)=12870 → Stichprobe
        idx = rng.choice(len(alle), max_splits, replace=False)
        alle = [alle[i] for i in idx]

    logits, unter_median = [], 0
    for is_idx in alle:
        oos_idx = [i for i in range(s) if i not in is_idx]
        is_r = pd.concat([bloecke[i] for i in is_idx])
        oos_r = pd.concat([bloecke[i] for i in oos_idx])

        is_sr = is_r.apply(sharpe)
        oos_sr = oos_r.apply(sharpe)
        if is_sr.isna().all() or oos_sr.isna().all():
            continue
        bester = is_sr.idxmax()
        # relativer OOS-Rang des IS-Siegers (1 = bester, 0 = schlechtester)
        rang = float(oos_sr.rank(pct=True)[bester])
        if rang < 0.5:
            unter_median += 1
        rang = min(max(rang, 1e-6), 1 - 1e-6)
        logits.append(math.log(rang / (1 - rang)))

    return {"pbo": unter_median / len(logits) if logits else np.nan,
            "n_splits": len(logits),
            "median_logit": float(np.median(logits)) if logits else np.nan}


def main() -> int:
    if not RET.exists():
        print("  ✗ ergebnisse/tagesrenditen.parquet fehlt — erst 03_backtest.py.")
        return 1

    rets = pd.read_parquet(RET)

    # ⚠️ BEIDE Tests laufen auf den EXCESS-Renditen gegen W0 (gleiches Overlay),
    # nicht auf den absoluten. Warum: der Sharpe eines Long-only-Aktien-
    # Sleeves ist im Wesentlichen der Markt-Sharpe — er misst, dass man in Aktien
    # investiert war, nicht dass die Rotation etwas konnte. Ein DSR auf absoluten
    # Renditen beantwortet die Frage „war Aktienbesitz 2014–2026 gut?" (ja, trivial)
    # statt „trägt die Rotation?". Der erste Lauf zeigte genau das: DSR = 0,999 für
    # ALLE 42 Konfigurationen — eine Zahl ohne Aussage.
    exc = pd.DataFrame({c: rets[c] - rets[f"{c.split('_')[0]}_W0_{c.split('_')[2]}"]
                        for c in rets.columns if c.split("_")[1] != "W0"})
    n_trials = rets.shape[1]                 # das GESAMTE Gitter ist der Preis
    alle_sr = np.array([sharpe(exc[c]) for c in exc.columns])

    print("=" * 78)
    print(f"  DEFLATED SHARPE RATIO auf EXCESS gegen W0 — {n_trials} Trials")
    print("=" * 78)
    print(f"    Ausgewertet: {len(exc.columns)} Rotations-Varianten "
          f"(W0 selbst hat keinen Excess gegen sich)")
    print(f"    SR-Streuung über die Varianten: σ = {np.nanstd(alle_sr, ddof=1):.3f}")
    ref = dsr(exc[exc.columns[0]], n_trials, alle_sr)
    print(f"    SR₀ = {ref['sr0_ann']:.3f}  ← so gut sieht die beste von {n_trials} "
          f"Varianten aus, wenn KEINE etwas kann")

    zeilen = []
    for c in exc.columns:
        d = dsr(exc[c], n_trials, alle_sr)
        d["konfig"] = c
        zeilen.append(d)
    df = pd.DataFrame(zeilen).set_index("konfig").sort_values("sr_ann", ascending=False)
    df.to_parquet(ERG / "overfitting.parquet", engine="pyarrow", compression="zstd")

    print(f"\n    {'Konfiguration':16} {'SR(exc)':>9} {'DSR':>8}   Lesart")
    for c in df.head(6).index:
        r = df.loc[c]
        lesart = ("überlebt Deflation" if r["dsr"] > 0.95 else
                  "grenzwertig" if r["dsr"] > 0.90 else "NICHT signifikant")
        print(f"    {c:16} {r['sr_ann']:9.3f} {r['dsr']:8.3f}   {lesart}")
    print(f"    … {len(df)-6} weitere")
    print(f"\n    Konfigurationen mit DSR > 0,95: {(df['dsr']>0.95).sum()} von {len(df)}")
    print(f"    Median DSR: {df['dsr'].median():.3f}")

    print("\n" + "=" * 78)
    print(f"  PBO via CSCV auf EXCESS — S = {S_BLOECKE} Blöcke")
    print("=" * 78)
    p = pbo_cscv(exc)
    print(f"    Aufteilungen ausgewertet: {p['n_splits']}")
    print(f"    PBO = {p['pbo']:.3f}")
    print(f"    Median-Logit = {p['median_logit']:+.3f}")
    urteil = ("✗ Die AUSWAHLPROZEDUR ist wertlos — der in-sample Sieger landet "
              "out-of-sample systematisch unter dem Median."
              if p["pbo"] > 0.5 else
              "✓ Die Auswahlprozedur trägt: der IS-Sieger bleibt OOS überwiegend "
              "über dem Median.")
    print(f"    {urteil}")
    print(f"\n  → ergebnisse/overfitting.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
