"""Schritt 6 — Block-Bootstrap + Permutationstest.

Der Bootstrap nimmt ausdrücklich das SCHÄRFERE Verfahren: nicht die Strategie-Renditen
resampeln (das testet nur „ist der Mittelwert > 0" mit der Regel als Konstante), sondern
das **Panel der Faktor-Renditen gemeinsam** — Spaltenstruktur erhalten, damit die
Cross-Korrelation überlebt — und dann **die Regel auf jedem Pfad neu laufen lassen**.
Das ist der Unterschied zwischen „hatte diese Renditereihe Glück" und „hat diese REGEL
auf Pfaden, auf denen sie nicht gefittet wurde, einen Vorteil".

Der Permutationstest ist der, der nicht bestechlich ist: Gewichtungsschema, Rebalance-Kalender,
Kosten und Turnover-Profil bleiben identisch — nur die Score-Zuordnung wird permutiert.
Liegt p > 0,10, ist die Rotation Dekoration auf einem Faktor-Korb.

⚠️ **BEWUSSTE ABWEICHUNG, ehrlich benannt:** Beide Verfahren laufen auf **Monatsbasis**,
nicht auf Tagesbasis. Der Tagesmotor (03) braucht ~0,5 s je Pfad ⇒ 10.000 Pfade wären
über eine Stunde je Verfahren. Der Monatsmotor ist ~30× schneller und für die Frage
äquivalent, weil die Strategie **monatlich** rebalanciert: zwischen zwei Rebalances
trägt der Tagespfad keine Entscheidung. Der z-Score läuft entsprechend über 12 Monate
statt 252 Handelstage. Was dadurch NICHT gemessen wird: der Overnight-Gap am
Rebalance-Tag und die Intramonats-Gewichtsdrift. Beides ist im Punktschätzer aus
Schritt 3/4 enthalten — hier geht es um die Verteilung, nicht um den Punkt.

    python 06_montecarlo.py [--pfade 10000] [--konfig S1_W1k2_O0]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HIER = Path(__file__).resolve().parent
PANEL = HIER / "daten" / "faktor_panel.parquet"
ERG = HIER / "ergebnisse"

FAKTOREN = ["VLUE", "QUAL", "MTUM", "IWF", "USMV", "SIZE"]
BENCH = "SPY"
KOSTEN = 0.0010
Z_FENSTER = 12          # Monate ≙ 252 HT
Z_MIN = 6


def monatspanel() -> tuple[np.ndarray, np.ndarray]:
    """(R_faktoren, r_bench) auf Monatsbasis, ab voller Verfügbarkeit."""
    panel = pd.read_parquet(PANEL)
    close = panel["close"][FAKTOREN + [BENCH]].dropna()
    m = (1 + close.pct_change()).resample("ME").prod() - 1
    m = m.dropna()
    return m[FAKTOREN].to_numpy(float), m[BENCH].to_numpy(float)


def scores_aus(R: np.ndarray, rb: np.ndarray) -> np.ndarray:
    """rs_ratio-Analogon auf Monatsbasis: z-Score des kumulierten RS-Verhältnisses."""
    rel = np.cumprod(1 + R, axis=0) / np.cumprod(1 + rb)[:, None]
    T, N = rel.shape
    S = np.full((T, N), np.nan)
    for t in range(Z_MIN, T):
        a, b = max(0, t - Z_FENSTER + 1), t + 1
        fenster = rel[a:b]
        mu, sd = fenster.mean(axis=0), fenster.std(axis=0, ddof=1)
        S[t] = np.where(sd > 0, (rel[t] - mu) / sd, np.nan)
    return S


def gewichte(s: np.ndarray, schema: str) -> np.ndarray:
    N = len(s)
    w = np.zeros(N)
    gueltig = ~np.isnan(s)
    if not gueltig.any():
        return w
    if schema == "W0":
        w[gueltig] = 1.0 / gueltig.sum()
    elif schema.startswith("W1k"):
        k = min(int(schema[3:]), int(gueltig.sum()))
        idx = np.where(gueltig)[0]
        top = idx[np.argsort(-s[idx])[:k]]
        w[top] = 1.0 / k
    elif schema.startswith("W2l"):
        lam = int(schema[3:]) / 100.0
        n = gueltig.sum()
        roh = np.zeros(N)
        roh[gueltig] = np.clip(1.0 / n + lam * s[gueltig], 0.0, 2.0 / n)
        w = roh / roh.sum() if roh.sum() > 0 else w
    return w


def fahre_monat(R: np.ndarray, S: np.ndarray, schema: str) -> np.ndarray:
    """Monats-Portfolio-Renditen. Signal aus t, Umsetzung in t+1 (kein Look-Ahead)."""
    T = len(R)
    out = np.zeros(T)
    w = np.zeros(R.shape[1])
    for t in range(1, T):
        w_neu = gewichte(S[t - 1], schema)
        to = np.abs(w_neu - w).sum() / 2.0
        out[t] = float(w_neu @ R[t]) - KOSTEN * to
        w = w_neu * (1 + R[t])
        w = w / w.sum() if w.sum() > 0 else w_neu
    return out[1:]


def ir(strat: np.ndarray, ref: np.ndarray) -> float:
    ex = strat - ref
    sd = ex.std(ddof=1)
    return float(ex.mean() * 12 / (sd * np.sqrt(12))) if sd > 0 else np.nan


def stationaer_bootstrap(n: int, L: float, rng) -> np.ndarray:
    """Politis/Romano: geometrische Blocklängen, Wrap-around."""
    idx = np.empty(n, dtype=int)
    i = rng.integers(n)
    for t in range(n):
        idx[t] = i
        if rng.random() < 1.0 / L:
            i = rng.integers(n)
        else:
            i = (i + 1) % n
    return idx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pfade", type=int, default=10000)
    ap.add_argument("--konfig", default="S1_W1k2_O0")
    a = ap.parse_args()

    schema = a.konfig.split("_")[1]
    R, rb = monatspanel()
    S = scores_aus(R, rb)
    T = len(R) - 1
    L = round(len(R) ** (1 / 3))

    beob_s = fahre_monat(R, S, schema)
    beob_w0 = fahre_monat(R, S, "W0")
    beob_ir = ir(beob_s, beob_w0)

    print("=" * 78)
    print(f"  MONTE CARLO — {a.konfig} (Schema {schema}) gegen W0")
    print("=" * 78)
    print(f"    Monate: {T}  ·  Blocklänge L = {L}  ·  Pfade: {a.pfade}")
    print(f"    Beobachtete IR (Monatsmotor): {beob_ir:+.3f}")

    rng = np.random.default_rng(2026)

    # ---------- Block-Bootstrap: Panel resampeln, REGEL neu laufen ----------
    print(f"\n  Stationärer Block-Bootstrap auf dem Input-Panel")
    print(f"    Lesart — **`P(IR≤0)` ist die Robustheitszahl**: auf wie vielen Pfaden,")
    print(f"    auf denen die Regel NICHT gefittet wurde, versagt sie? Der Rang des")
    print(f"    beobachteten Werts ist KEIN Signifikanztest (die Regel läuft auf jedem")
    print(f"    Pfad neu — ein mittlerer Rang bei positivem Median ist das GUTE Ergebnis).")
    ergebnisse = {}
    for faktor, lab in ((0.5, "L/2"), (1.0, "L"), (2.0, "2L")):
        Lx = max(1.5, L * faktor)
        irs = np.empty(a.pfade)
        for p in range(a.pfade):
            idx = stationaer_bootstrap(len(R), Lx, rng)
            Rp, rbp = R[idx], rb[idx]
            Sp = scores_aus(Rp, rbp)
            irs[p] = ir(fahre_monat(Rp, Sp, schema), fahre_monat(Rp, Sp, "W0"))
        irs = irs[np.isfinite(irs)]
        ergebnisse[lab] = irs
        print(f"    {lab:4} (L={Lx:4.1f})  IR-Median {np.median(irs):+.3f}  "
              f"p5 {np.percentile(irs,5):+.3f}  p95 {np.percentile(irs,95):+.3f}  "
              f"P(IR≤0) {float((irs<=0).mean()):.3f}  "
              f"[Rang beob.: {float((irs>=beob_ir).mean()):.2f}]")

    # ---------- Permutationstest ----------
    print(f"\n  Permutationstest — Score-Zuordnung zufällig, alles andere identisch")
    null_ir = np.empty(a.pfade)
    for p in range(a.pfade):
        Sp = S.copy()
        for t in range(len(Sp)):
            if np.isfinite(Sp[t]).any():
                Sp[t] = Sp[t][rng.permutation(Sp.shape[1])]
        null_ir[p] = ir(fahre_monat(R, Sp, schema), beob_w0)
    null_ir = null_ir[np.isfinite(null_ir)]
    p_perm = float((null_ir >= beob_ir).mean())

    print(f"    Null-Verteilung: Median {np.median(null_ir):+.3f}  "
          f"p95 {np.percentile(null_ir,95):+.3f}")
    print(f"    p = P(IR_null ≥ IR_beob) = {p_perm:.4f}")
    urteil = ("✗ p > 0,10 — die Rotation ist DEKORATION auf einem Faktor-Korb. "
              "Die Antwort auf die Ausgangsfrage lautet NEIN, mit Zahl."
              if p_perm > 0.10 else
              "✓ p ≤ 0,10 — ein bedeutungsloser Score erzeugt dieses Ergebnis selten.")
    print(f"    {urteil}")

    np.savez(ERG / "montecarlo.npz", beob_ir=beob_ir, null_ir=null_ir,
             **{f"boot_{k}": v for k, v in ergebnisse.items()})
    print(f"\n  → ergebnisse/montecarlo.npz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
