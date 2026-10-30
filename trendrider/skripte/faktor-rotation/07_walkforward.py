"""Schritt 7 — Walk-Forward.

    Train 60 Monate → Embargo 1 Monat → Test 12 Monate → rollen.

Das Embargo ist bewusst **ein Monat**, nicht 20 Handelstage: der längste Horizont
dieser Strategie ist ein Rebalance-Intervall, und ein Embargo muss ihn abdecken.

**Berichtet wird ausschließlich die aneinandergehängte Out-of-Window-Kurve.** In jedem
Fenster wird auf den Trainingsdaten die beste Konfiguration gewählt und dann *blind* auf
dem Testfenster gefahren — das ist die einzige Zahl, die simuliert, was jemand hätte
erleben können, der die Auswahl nicht schon kannte.

Bei 156 Monaten sind das ~6 Testfenster. Das ist wenig, und das gehört so gesagt.

⚠️ **Diese Messung hat keinen Vorwärtstest-Schutz:** Es gibt keine live geführte
Watchlist, die Historie ist alles. Deshalb sind DSR/PBO (Schritt 5) und dieser
Walk-Forward nicht optional — sie ersetzen strukturell, was sonst ein laufender
Vorwärtstest leistet.

    python 07_walkforward.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HIER = Path(__file__).resolve().parent
ERG = HIER / "ergebnisse"
RET = ERG / "tagesrenditen.parquet"

TRAIN_M, EMBARGO_M, TEST_M = 60, 1, 12


def ir_monat(strat: pd.Series, ref: pd.Series) -> float:
    ex = (strat - ref).dropna()
    sd = ex.std(ddof=1)
    return float(ex.mean() * 12 / (sd * np.sqrt(12))) if sd > 0 else np.nan


def main() -> int:
    if not RET.exists():
        print("  ✗ ergebnisse/tagesrenditen.parquet fehlt.")
        return 1

    rets = pd.read_parquet(RET)
    monatlich = (1 + rets).resample("ME").prod() - 1
    kandidaten = [c for c in monatlich.columns if c.split("_")[1] != "W0"]
    monate = monatlich.index
    n = len(monate)

    print("=" * 78)
    print(f"  WALK-FORWARD — Train {TRAIN_M} M → Embargo {EMBARGO_M} M → "
          f"Test {TEST_M} M")
    print("=" * 78)
    print(f"    {n} Monate gesamt · {len(kandidaten)} Kandidaten je Fenster\n")
    print(f"    {'Fenster':22} {'gewählt (IS)':16} {'IS-IR':>7} {'OOS-IR':>8}  Urteil")

    oos_teile, zeilen = [], []
    start = 0
    while start + TRAIN_M + EMBARGO_M + TEST_M <= n:
        tr = monatlich.iloc[start:start + TRAIN_M]
        te = monatlich.iloc[start + TRAIN_M + EMBARGO_M:
                            start + TRAIN_M + EMBARGO_M + TEST_M]

        irs = {c: ir_monat(tr[c], tr[f"{c.split('_')[0]}_W0_{c.split('_')[2]}"])
               for c in kandidaten}
        bester = max(irs, key=lambda k: (irs[k] if np.isfinite(irs[k]) else -9e9))
        ref_te = te[f"{bester.split('_')[0]}_W0_{bester.split('_')[2]}"]
        oos = ir_monat(te[bester], ref_te)

        oos_teile.append((te[bester] - ref_te))
        zeilen.append({"fenster": f"{te.index[0]:%Y-%m}→{te.index[-1]:%Y-%m}",
                       "gewaehlt": bester, "is_ir": irs[bester], "oos_ir": oos})
        print(f"    {zeilen[-1]['fenster']:22} {bester:16} {irs[bester]:7.2f} "
              f"{oos:8.2f}  {'✓' if oos > 0 else '✗'}")
        start += TEST_M

    if not zeilen:
        print("    Zu wenig Historie für ein vollständiges Fenster.")
        return 1

    df = pd.DataFrame(zeilen)
    ex = pd.concat(oos_teile)
    sd = ex.std(ddof=1)
    ir_gesamt = float(ex.mean() * 12 / (sd * np.sqrt(12))) if sd > 0 else np.nan

    print("\n" + "-" * 78)
    print(f"    Fenster gesamt:                {len(df)}")
    print(f"    davon OOS-IR > 0:              {(df['oos_ir'] > 0).sum()} von {len(df)}")
    print(f"    Ø IS-IR (was man sah):         {df['is_ir'].mean():+.2f}")
    print(f"    Ø OOS-IR (was man bekam):      {df['oos_ir'].mean():+.2f}")
    print(f"    Schwund IS → OOS:              "
          f"{(df['is_ir'].mean() - df['oos_ir'].mean()):+.2f}")
    print(f"\n    **Aneinandergehängte OOS-Kurve — die einzige ehrliche Zahl:**")
    print(f"      IR = {ir_gesamt:+.3f}   über {len(ex)} Monate")
    print(f"      Excess p.a. = {ex.mean()*12*100:+.2f} %   "
          f"Hit-Rate = {(ex > 0).mean()*100:.0f} %")

    df.to_parquet(ERG / "walkforward.parquet", engine="pyarrow", compression="zstd")
    print(f"\n  → ergebnisse/walkforward.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
