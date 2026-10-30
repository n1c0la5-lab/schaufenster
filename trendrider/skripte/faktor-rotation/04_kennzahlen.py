"""Schritt 4 — Kennzahlen + Gitter.

**Leitkennzahl ist die Information Ratio gegen W0, nicht der Sharpe**: Der Sharpe
eines Long-only-Aktien-Sleeves ist im Wesentlichen der Markt-Sharpe plus Rauschen — er
misst, dass man in Aktien investiert war, nicht dass die Rotation etwas konnte. Die IR
gegen die Gleichgewichtung isoliert exakt die Rotationsentscheidung.

**Referenz je Zelle ist W0 mit DEMSELBEN Overlay.** Sonst vermischt der Excess zwei
Effekte (Rotation + Overlay) und die Zahl beantwortet keine der beiden Fragen. Zusätzlich
ausgewiesen: IR gegen das nackte `W0_O0` — das ist der Vergleich „Strategie gegen die
einfachste denkbare Umsetzung".

**Berichtsform: ein Gitter, keine Bestwert-Zeile.** Ein Ergebnis zählt nur, wenn
ein *zusammenhängendes Feld* benachbarter Zellen trägt; ein einzelner heller Punkt in
einer dunklen Matrix ist eine Zufallszahl mit Koordinaten.

    python 04_kennzahlen.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HIER = Path(__file__).resolve().parent
ERG = HIER / "ergebnisse"
RET = ERG / "tagesrenditen.parquet"
UEB = ERG / "lauf_uebersicht.parquet"
RF = HIER / "daten" / "riskfree.parquet"

SCORES = ["S1", "S2"]
GEWICHTE = ["W0", "W1k1", "W1k2", "W1k3", "W2l10", "W2l20", "W2l40"]
OVERLAYS = ["O0", "O1", "O2"]
TER_HUERDE = 0.0033      # TER eines fertigen Faktor-Fonds — darunter ist der Fonds die billigere Umsetzung
ETF_HUERDE = 0.0023      # gegen einen 0,10 %-Welt-ETF


def kennzahlen(r: pd.Series, rf_d: pd.Series) -> dict:
    r = r.dropna()
    j = len(r) / 252
    eq = (1 + r).cumprod()
    rf = rf_d.reindex(r.index).fillna(0.0)
    ex = r - rf
    vol = r.std(ddof=1) * np.sqrt(252)
    down = r[r < 0].std(ddof=1) * np.sqrt(252)
    peak = eq.cummax()
    mdd = float(((peak - eq) / peak).max())
    cagr = float(eq.iloc[-1] ** (1 / j) - 1)
    return {
        "cagr": cagr,
        "vol": float(vol),
        "sharpe": float(ex.mean() / r.std(ddof=1) * np.sqrt(252)) if r.std(ddof=1) > 0 else np.nan,
        "sortino": float(ex.mean() * 252 / down) if down and down > 0 else np.nan,
        "maxdd": mdd,
        "calmar": float(cagr / mdd) if mdd > 0 else np.nan,
    }


def rel_kennzahlen(r: pd.Series, ref: pd.Series) -> dict:
    """Alles gegen die Referenz. Monatsbasis für TE/IR (Rebalance-Frequenz)."""
    a, b = r.align(ref, join="inner")
    ex_d = (a - b).dropna()
    ex_m = ((1 + a).resample("ME").prod() - (1 + b).resample("ME").prod()).dropna()
    te = float(ex_m.std(ddof=1) * np.sqrt(12))
    return {
        "excess_pa": float(ex_d.mean() * 252),
        "te": te,
        "ir": float(ex_m.mean() * 12 / te) if te > 0 else np.nan,
        "hitrate_m": float((ex_m > 0).mean()),
        "n_monate": int(len(ex_m)),
    }


def main() -> int:
    for p in (RET, UEB, RF):
        if not p.exists():
            print(f"  ✗ fehlt: {p.name}")
            return 1

    rets = pd.read_parquet(RET)
    ueb = pd.read_parquet(UEB)
    rf_d = pd.read_parquet(RF)["dgs3mo_pct"] / 100.0 / 252.0
    rf_d.index = pd.to_datetime(rf_d.index)
    rf_d = rf_d.reindex(rets.index).ffill().fillna(0.0)

    zeilen = []
    for k in rets.columns:
        sc, gw, ov = k.split("_")
        m = kennzahlen(rets[k], rf_d)
        m |= {"konfig": k, "score": sc, "gewicht": gw, "overlay": ov}
        # Referenz 1: W0 mit demselben Overlay (isoliert die Rotation)
        ref_gleich = f"{sc}_W0_{ov}"
        m |= {f"{x}_vs_w0": v for x, v in rel_kennzahlen(rets[k], rets[ref_gleich]).items()}
        # Referenz 2: das nackte W0_O0
        m |= {f"{x}_vs_basis": v for x, v in
              rel_kennzahlen(rets[k], rets["S1_W0_O0"]).items()}
        m["turnover_pa"] = float(ueb.loc[k, "turnover_pa"])
        m["halter"] = float(ueb.loc[k, "halter"])
        zeilen.append(m)

    df = pd.DataFrame(zeilen).set_index("konfig")
    df.to_parquet(ERG / "kennzahlen.parquet", engine="pyarrow", compression="zstd")

    # ---------------- Ausgabe ----------------
    ref = df.loc["S1_W0_O0"]
    print("=" * 78)
    print("  REFERENZ  W0 · Gleichgewicht sechs Faktoren, kein Overlay")
    print("=" * 78)
    print(f"    CAGR {ref['cagr']*100:6.2f} %   Vol {ref['vol']*100:5.2f} %   "
          f"Sharpe {ref['sharpe']:5.2f}   MaxDD {ref['maxdd']*100:5.1f} %   "
          f"Calmar {ref['calmar']:4.2f}")
    print(f"    Beobachtungszeitraum: {rets.index[0].date()} → {rets.index[-1].date()}  "
          f"({ref['n_monate_vs_basis']} Monate)")

    print("\n" + "=" * 78)
    print("  GITTER — Information Ratio gegen W0 (gleiches Overlay)")
    print("  Ein einzelner heller Punkt ist eine Zufallszahl. Gesucht: ein FELD.")
    print("=" * 78)
    for ov in OVERLAYS:
        print(f"\n  Overlay {ov}")
        print(f"    {'Gewicht':8} " + "".join(f"{s:>12}" for s in SCORES) + "     Turnover")
        for gw in GEWICHTE:
            zeile = f"    {gw:8} "
            to = np.nan
            for sc in SCORES:
                k = f"{sc}_{gw}_{ov}"
                ir = df.loc[k, "ir_vs_w0"]
                to = df.loc[k, "turnover_pa"]
                zeile += "         —  " if gw == "W0" else f"{ir:12.2f}"
            zeile += f"     {to*100:6.1f} %/J"
            print(zeile)

    print("\n" + "=" * 78)
    print("  HÜRDEN — schlägt die Rotation W0 um mehr als die Gebühr?")
    print("=" * 78)
    kand = df[df["gewicht"] != "W0"].copy()
    kand["ueber_ter"] = kand["excess_pa_vs_w0"] > TER_HUERDE
    kand["ueber_etf"] = kand["excess_pa_vs_w0"] > ETF_HUERDE
    print(f"    Konfigurationen gesamt (ohne W0):        {len(kand)}")
    print(f"    davon Excess p.a. > 0:                   {(kand['excess_pa_vs_w0']>0).sum()}")
    print(f"    davon > 0,23 %/J (Welt-ETF-Hürde):       {kand['ueber_etf'].sum()}")
    print(f"    davon > 0,33 %/J (Fonds-TER-Hürde):      {kand['ueber_ter'].sum()}")
    print(f"    beste IR im Gitter:                      {kand['ir_vs_w0'].max():.2f}"
          f"   ({kand['ir_vs_w0'].idxmax()})")
    print(f"    Median IR über alle Konfigurationen:     {kand['ir_vs_w0'].median():.2f}")
    print(f"    Anteil Konfigurationen mit IR > 0:       "
          f"{(kand['ir_vs_w0']>0).mean()*100:.0f} %")
    print(f"\n  → ergebnisse/kennzahlen.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
