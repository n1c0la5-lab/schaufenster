"""Kuendigen sich schwere Einbrueche an? - ein Einwand, gemessen.

Der Einwand: "Survivorship ist halb so schlimm, weil Sektor-Rotation und der
Marktfilter laufend NEUE Ueberlebende hervorbringen." Das stimmt genau dann, wenn die
Rotation einen Titel rauswirft, BEVOR der Einbruch das Geld kostet. Also:

  Wenn ein Titel vom 252-Tage-Hoch um 60/70/80 % faellt -
  wie viel davon war beim EMA150-Bruch schon gelaufen?

Ist beim Warnsignal erst wenig Verlust aufgelaufen, traegt das Argument.
Ist der Bruch selbst schon tief im Minus, raeumt die Rotation hinterher auf,
statt zu schuetzen - und der Kipppunkt aus ../rebalancing/ gilt.

⚠️ UNTERE SCHRANKE: Diese 484 Titel haben alle ueberlebt. Wer nie zurueckkam,
fehlt. Die echte Haeufigkeit schwerer Einbrueche ist also HOEHER als hier.
Genau darum ist die Haeufigkeit hier nicht die Aussage - die VORWARNUNG ist es.
"""
import json, glob, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "..", "daten", "historie")
HOCH_N, EMA_N = 252, 150

def ema(x, n):
    a = 2.0 / (n + 1.0); out = np.empty_like(x); out[0] = x[0]
    for i in range(1, len(x)): out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out

episoden, titel_jahre, n_titel = [], 0.0, 0
for f in sorted(glob.glob(f"{HIST}/*.json")):
    d = json.load(open(f)); sym = d["symbol"]
    bars = [b for b in d["bars"] if b.get("close") and b["close"] > 0]
    if len(bars) < 400: continue
    c = np.array([b["close"] for b in bars]); dt = [b["bar_date"] for b in bars]
    n_titel += 1; titel_jahre += len(c) / 252.0
    e = ema(c, EMA_N)
    hoch = np.array([c[max(0, i - HOCH_N):i + 1].max() for i in range(len(c))])
    dd = c / hoch - 1.0
    i = EMA_N
    while i < len(c):
        if dd[i] <= -0.60:
            # Episode: zurueck zum Hoch, das diesen Drawdown erzeugt
            j = i
            while j > 0 and c[j - 1] >= c[j]: j -= 1
            start = int(np.argmax(c[max(0, i - HOCH_N):i + 1])) + max(0, i - HOCH_N)
            peak = c[start]
            # letzter EMA150-Bruch zwischen Hoch und -60 %
            bruch = None
            for k in range(start + 1, i + 1):
                if c[k] < e[k] and c[k - 1] >= e[k - 1]: bruch = k
            tief = int(np.argmin(c[start:i + 1])) + start
            episoden.append(dict(
                sym=sym, hoch=dt[start], tief=dt[tief],
                dd_min=float(c[tief] / peak - 1.0),
                bruch_tage=None if bruch is None else int(i - bruch),
                dd_bei_bruch=None if bruch is None else float(c[bruch] / peak - 1.0),
                tage_hoch_bis_60=int(i - start)))
            # weiter nach der Erholung ueber -30 %
            while i < len(c) and dd[i] < -0.30: i += 1
        i += 1

print(f"Titel: {n_titel} · Titel-Jahre: {titel_jahre:.0f}")
print(f"Episoden mit Drawdown <= -60 %: {len(episoden)}")
print(f"Rate: {len(episoden)/titel_jahre:.2%} je Titel und Jahr  (UNTERE Schranke)")

mb = [e for e in episoden if e["dd_bei_bruch"] is not None]
print(f"\ndavon mit EMA150-Bruch zwischen Hoch und -60 %: {len(mb)} ({len(mb)/max(len(episoden),1):.0%})")
if mb:
    v = np.array([e["dd_bei_bruch"] for e in mb])
    t = np.array([e["bruch_tage"] for e in mb])
    print(f"\n=== Wie viel Verlust war beim EMA150-Bruch schon gelaufen? ===")
    for p in (10, 25, 50, 75, 90):
        print(f"    p{p:<3} {np.percentile(v,p):>7.1%}")
    print(f"    Mittel {v.mean():>6.1%}")
    print(f"\n=== Handelstage vom EMA150-Bruch bis -60 % ===")
    for p in (10, 25, 50, 75, 90):
        print(f"    p{p:<3} {np.percentile(t,p):>6.0f} HT")
    print(f"\n    Anteil, bei denen der Bruch spaeter als 2 Wochen vor -60 % kam: "
          f"{(t>10).mean():.0%}")
    print(f"    Anteil, bei denen beim Bruch schon mehr als -30 % gelaufen war: "
          f"{(v<-0.30).mean():.0%}")
json.dump(episoden, open(f"{HERE}/episoden.json", "w"), indent=1)
print(f"\n→ {len(episoden)} Episoden in episoden.json")
