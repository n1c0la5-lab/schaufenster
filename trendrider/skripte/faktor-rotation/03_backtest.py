"""Schritt 3 — Backtest-Motor.

Fährt das vollständige Varianten-Gitter: 2 Scores × 7 Gewichte × 3 Overlays
= **42 Konfigurationen**. Keine wird bevorzugt, keine weggelassen — die Zahl geht als
`trials` in die Deflated Sharpe Ratio (Schritt 5).

MODELLIERUNG, die der Vorab-Spezifikation folgt statt sie zu vereinfachen:

* **Signal am letzten Handelstag des Monats (t_M), Entry zum OPEN t_M+1** (schließt
  Look-Ahead aus). Der Rebalance-Tag wird deshalb zweigeteilt gerechnet: alte Gewichte
  bis zum Open, neue vom Open bis zum Close. Wer nur Close-zu-Close rechnet, verschenkt
  genau den Overnight-Gap, an dem der Wechsel stattfindet.
* **Gewichte driften zwischen den Rebalances** (Buy-and-Hold). Das ist nicht Kosmetik:
  ohne Drift wäre der Turnover systematisch überschätzt und die Kostenlast erfunden.
* **Kosten auf den UMGESETZTEN Turnover**: 0,10 % Round-Trip auf ½·Σ|Δw|.
  Halten kostet nichts.
* **Auflagedaten hart**: vor dem Listing ist das Gewicht 0, der Rest wird
  normiert — kein NaN-Füllen, keine Rückrechnung auf Instrumente, die es nicht gab.

    python 03_backtest.py            # alle 42 Konfigurationen
    python 03_backtest.py --nur W0   # eine Gewichtung (Diagnose)
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HIER = Path(__file__).resolve().parent
PANEL = HIER / "daten" / "faktor_panel.parquet"
SIGNAL = HIER / "daten" / "signal.parquet"
RF = HIER / "daten" / "riskfree.parquet"
ERG = HIER / "ergebnisse"

FAKTOREN = ["VLUE", "QUAL", "MTUM", "IWF", "USMV", "SIZE"]
BENCH = "SPY"
N = len(FAKTOREN)
KOSTEN = 0.0010          # Round-Trip auf umgesetzten Turnover
AUFLAGE = {"VLUE": "2013-04-18", "QUAL": "2013-07-18", "MTUM": "2013-04-18",
           "IWF": "2013-01-02", "USMV": "2013-01-02", "SIZE": "2013-04-18"}

# Gitter — vollständig, nichts versteckt.
SCORES = ["S1", "S2"]
GEWICHTE = ["W0", "W1k1", "W1k2", "W1k3", "W2l10", "W2l20", "W2l40"]
OVERLAYS = ["O0", "O1", "O2"]
VOL_ZIEL = 0.12          # O2: 12 % p.a.
VOL_FENSTER = 60         # Handelstage realisierte Vola


def gewichte(scores: pd.Series, schema: str, verfuegbar: pd.Index) -> pd.Series:
    """Zielgewichte am Signaltag. `verfuegbar` = gelistete Faktoren.

    ⚠️ **W0 ist bewusst SCORE-UNABHÄNGIG.** Gleichgewichtung braucht keinen Score, und
    W0 ist die Referenz, gegen die alles gemessen wird. Würde W0 — wie die
    Score-Schemata — nur über Faktoren mit gültigem Score gleichgewichten, gäbe es zwei
    verschiedene Referenzen (eine je Score-Variante), und die IR wäre keine Aussage über
    die Rotation mehr, sondern über die Warm-up-Länge von `rs_mom`. Erster Lauf zeigte
    genau das: S1_W0_O0 13,54 % vs. S2_W0_O0 13,05 % CAGR bei identischer Strategie.
    """
    w = pd.Series(0.0, index=FAKTOREN)
    if schema == "W0":
        if len(verfuegbar):
            w.loc[verfuegbar] = 1.0 / len(verfuegbar)
        return w

    s = scores.reindex(verfuegbar).dropna()
    if s.empty:
        return w
    n = len(s)

    if schema.startswith("W1k"):
        k = min(int(schema[3:]), n)
        top = s.nlargest(k).index
        w.loc[top] = 1.0 / k
    elif schema.startswith("W2l"):
        lam = int(schema[3:]) / 100.0
        roh = (1.0 / n + lam * s).clip(lower=0.0, upper=2.0 / n)
        w.loc[s.index] = (roh / roh.sum()) if roh.sum() > 0 else 1.0 / n
    return w


def overlay_quote(tag: pd.Timestamp, schema: str, spy: pd.Series,
                  port_ret: pd.Series) -> float:
    """Aktienquote am Signaltag (Rest = Cash). Nur Information bis t_M — kein Blick voraus."""
    if schema == "O0":
        return 1.0
    if schema == "O1":
        hist = spy.loc[:tag]
        if len(hist) < 200:
            return 1.0
        ema200 = hist.ewm(span=200, adjust=False).mean().iloc[-1]
        return 0.5 if hist.iloc[-1] < ema200 else 1.0
    if schema == "O2":
        hist = port_ret.loc[:tag].dropna()
        if len(hist) < VOL_FENSTER:
            return 1.0
        vol = hist.iloc[-VOL_FENSTER:].std(ddof=1) * np.sqrt(252)
        if vol <= 0 or not np.isfinite(vol):
            return 1.0
        return float(np.clip(VOL_ZIEL / vol, 0.0, 1.0))    # kein Hebel
    return 1.0


def fahre(panel: pd.DataFrame, sig: pd.DataFrame, rf_d: pd.Series,
          score: str, schema: str, overlay: str) -> dict:
    """Kern auf numpy. Alles, was nicht vom Pfad abhängt, wird VOR der Schleife
    gerechnet — `close.shift(1)` oder ein wachsendes Series-Objekt in der Tagesschleife
    machen den Lauf O(n²) und den Monte Carlo (Schritt 6, 10.000 Pfade) unmöglich."""
    close, open_ = panel["close"], panel["open"]
    idx = sig["ratio"].dropna().index                     # alle 6 Faktoren gültig
    idx = idx[idx >= pd.Timestamp("2014-01-01")]
    T, Nf = len(idx), len(FAKTOREN)

    C = close.loc[idx, FAKTOREN].to_numpy(float)
    O = open_.loc[idx, FAKTOREN].to_numpy(float)
    C_prev = np.vstack([C[:1], C[:-1]])
    G_OPEN = np.nan_to_num(O / C_prev, nan=1.0, posinf=1.0, neginf=1.0)   # PrevClose→Open
    G_CLOSE = np.nan_to_num(C / O, nan=1.0, posinf=1.0, neginf=1.0)       # Open→Close
    G_DAY = np.nan_to_num(C / C_prev, nan=1.0, posinf=1.0, neginf=1.0)    # Close→Close

    s_ratio = (sig["ratio"].loc[idx, FAKTOREN] - 100.0).to_numpy(float)
    SC = s_ratio if score == "S1" else s_ratio + (sig["mom"].loc[idx, FAKTOREN] - 100.0).to_numpy(float)

    RF = rf_d.reindex(idx).to_numpy(float)
    RF = np.nan_to_num(RF, nan=0.0)

    # Auflage-Maske: vor dem Listing kein Gewicht.
    auf = np.array([[pd.Timestamp(AUFLAGE[f]) <= d for f in FAKTOREN] for d in idx])

    # O1 ist strategie-unabhängig → einmal vorberechnen.
    spy = close.loc[idx, BENCH]
    unter_ema200 = (spy < spy.ewm(span=200, adjust=False).mean()).to_numpy()
    warm200 = np.arange(T) < 200

    # Rebalance-Positionen: letzter Handelstag je Monat, Umsetzung am Folgetag.
    pos_letzter = pd.Series(np.arange(T), index=idx).groupby(idx.to_period("M")).last()
    umsetzung = {int(p) + 1: int(p) for p in pos_letzter if int(p) + 1 < T}

    w = np.zeros(Nf)
    V = 1.0
    equity = np.empty(T)
    tagesret = np.empty(T)
    port_ret = np.empty(T)
    halter = np.empty(T, dtype=int)
    turnover = []

    for t in range(T):
        rf_t = RF[t]
        if t in umsetzung:                                 # --- Rebalance-Tag ---
            m = umsetzung[t]
            # 1) alte Positionen bis zum Open
            wert_alt = float(w @ G_OPEN[t]) + (1.0 - w.sum()) * (1.0 + rf_t)
            w_open = (w * G_OPEN[t]) / wert_alt if wert_alt > 0 else w
            V_open = V * wert_alt

            # 2) Zielgewichte aus dem Signal von t_M
            verf = pd.Index([f for i, f in enumerate(FAKTOREN) if auf[m, i]])
            w_ziel = gewichte(pd.Series(SC[m], index=FAKTOREN), schema, verf).to_numpy()

            if overlay == "O0":
                quote = 1.0
            elif overlay == "O1":
                quote = 1.0 if warm200[m] else (0.5 if unter_ema200[m] else 1.0)
            else:                                          # O2 Vol-Target
                if m < VOL_FENSTER:
                    quote = 1.0
                else:
                    vol = port_ret[m - VOL_FENSTER:m].std(ddof=1) * np.sqrt(252)
                    quote = float(np.clip(VOL_ZIEL / vol, 0.0, 1.0)) if vol > 0 else 1.0
            w_neu = w_ziel * quote

            # 3) Kosten auf den umgesetzten Turnover
            to = float(np.abs(w_neu - w_open).sum()) / 2.0
            V_open *= (1.0 - KOSTEN * to)
            turnover.append(to)

            # 4) Open → Close mit den neuen Gewichten
            wert_neu = float(w_neu @ G_CLOSE[t]) + (1.0 - w_neu.sum()) * (1.0 + rf_t / 2)
            V_neu = V_open * wert_neu
            w = (w_neu * G_CLOSE[t]) / wert_neu if wert_neu > 0 else w_neu
            tag_r = V_neu / V - 1.0
            V = V_neu
        else:                                              # --- normaler Tag ---
            wert = float(w @ G_DAY[t]) + (1.0 - w.sum()) * (1.0 + rf_t)
            w = (w * G_DAY[t]) / wert if wert > 0 else w
            tag_r = wert - 1.0
            V *= wert

        equity[t] = V
        tagesret[t] = tag_r
        port_ret[t] = tag_r
        halter[t] = int((w > 1e-6).sum())

    return {
        "equity": pd.Series(equity, index=idx),
        "ret": pd.Series(tagesret, index=idx),
        "turnover_pa": float(np.sum(turnover) / (T / 252)),
        "halter": float(halter.mean()),
        "rebalances": len(turnover),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur", help="nur ein Gewichtsschema (Diagnose)")
    a = ap.parse_args()

    for p in (PANEL, SIGNAL, RF):
        if not p.exists():
            print(f"  ✗ fehlt: {p.name} — vorherige Schritte laufen lassen.")
            return 1

    panel = pd.read_parquet(PANEL)
    sig = pd.read_parquet(SIGNAL)
    rf_pct = pd.read_parquet(RF)["dgs3mo_pct"]
    rf_d = (rf_pct / 100.0 / 252.0).reindex(panel.index).ffill().fillna(0.0)

    schemata = [a.nur] if a.nur else GEWICHTE
    ERG.mkdir(exist_ok=True)
    zeilen, kurven = [], {}

    print(f"  Gitter: {len(SCORES)} Scores × {len(schemata)} Gewichte × "
          f"{len(OVERLAYS)} Overlays = {len(SCORES)*len(schemata)*len(OVERLAYS)} Konfigurationen\n")
    for sc, gw, ov in itertools.product(SCORES, schemata, OVERLAYS):
        r = fahre(panel, sig, rf_d, sc, gw, ov)
        name = f"{sc}_{gw}_{ov}"
        kurven[name] = r["ret"]
        j = len(r["ret"]) / 252
        cagr = r["equity"].iloc[-1] ** (1 / j) - 1
        zeilen.append({"konfig": name, "score": sc, "gewicht": gw, "overlay": ov,
                       "cagr": cagr, "endwert": float(r["equity"].iloc[-1]),
                       "turnover_pa": r["turnover_pa"], "halter": r["halter"],
                       "rebalances": r["rebalances"]})
        print(f"    {name:16} CAGR {cagr*100:6.2f} %   Turnover {r['turnover_pa']*100:6.1f} %/J"
              f"   Ø Halter {r['halter']:.1f}")

    pd.DataFrame(kurven).to_parquet(ERG / "tagesrenditen.parquet",
                                    engine="pyarrow", compression="zstd")
    df = pd.DataFrame(zeilen).set_index("konfig")
    df.to_parquet(ERG / "lauf_uebersicht.parquet", engine="pyarrow", compression="zstd")

    ref = df.loc["S1_W0_O0"] if "S1_W0_O0" in df.index else None
    print(f"\n  {len(df)} Konfigurationen gefahren, {df['rebalances'].iloc[0]} Rebalances je Lauf.")
    if ref is not None:
        print(f"  Referenz W0 (der eigentliche Gegner): CAGR {ref['cagr']*100:.2f} %, "
              f"Turnover {ref['turnover_pa']*100:.1f} %/J")
    print(f"  → ergebnisse/tagesrenditen.parquet + lauf_uebersicht.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
