# CLAUDE.md — Strandgut
*Beach-Log und Content-Maschine für die Treibholz-Reise.*

## Was ist das hier?

Dies ist die Content-Pipeline für eine reisende Treibholz-Marke (Beispiel: DriftCraft.eu — setz deinen eigenen Namen ein). Ein Maker zieht mit dem Camper an europäischen Küsten entlang, sammelt Treibholz, baut daraus Türgriffe und Möbelbeschläge, und verkauft sie
über einen eigenen Web-Shop. Diese Pipeline ist die Erzählmaschine dahinter.

**Kernidee:** Eine Eingabe vom Strand wird zu fünf Ausgaben im Netz.

```
   Voice Memo  ─┐
   GPS-Pin     ─┤
   Strandfoto  ─┼──►  Pipeline  ──►  Blog-Post
   Wetter      ─┤                    Pinterest-Pin
   Holz-Fund   ─┘                    Instagram-Caption
                                     Newsletter-Absatz
                                     Astro e-commerce-Produkt
```

**Kein SaaS, kein Airtable, kein Tracker.** Alles lokal im Vault.
Frontmatter ist die einzige Wahrheit.

---

## Struktur

```
strandgut/
├── CLAUDE.md                  ← Du bist hier
├── kontext/
│   ├── marke.md               ← Stimme, Story, Werte, was wir nicht sind
│   ├── zielgruppe.md          ← Wer kauft, wer liest, wer folgt
│   └── kuesten.md             ← Wo gesammelt werden darf, pro Land
├── skills/
│   ├── feld-log.md            ← /feld   — Roh-Eintrag vom Strand
│   ├── stueck-story.md        ← /stueck — Aus Fund wird Produkt mit Story
│   ├── reise-tag.md           ← /tag    — Tag → Blog + Social + Newsletter
│   ├── shop-listing.md        ← /shop   — Aus Stück wird Astro.build-Produkt
│   └── monats-rueckblick.md   ← /monat  — Monat zusammenfassen
├── logbuch/                   ← Roh-Einträge vom Strand (Datum)
│   └── YYYY-MM-DD.md
├── stuecke/                   ← Pro Holzstück eine Datei
│   └── stueck-NNNN.md
└── outputs/
    ├── blog/                  ← Reise-Posts, Story-Artikel
    ├── social/                ← Pinterest + Instagram-Drafts
    ├── newsletter/            ← Wochen- oder Drop-Mails
    └── sanity/               ← Produkt-Beschreibungen, ready to upload
```

---

## Workflow

```
   STRAND                     WERKSTATT                 NETZ
  ────────                   ───────────              ────────

  /feld          ──►   logbuch/2026-04-29.md
   (am Abend
    am Lagerfeuer)

                                                        
                          /stueck       ──►   stuecke/stueck-0042.md
                           (Foto + Maße,                (Status: roh →
                            Notiz zur Idee)              geschliffen →
                                                         fertig → verkauft)

                                                          
                          /tag          ──►   outputs/blog/2026-04-29.md
                           (aus Logbuch              outputs/social/2026-04-29.md
                            + Stücken)              outputs/newsletter/woche-17.md


                          /shop         ──►   outputs/sanity/stueck-0042.md
                           (wenn Stück
                            fertig ist)
```

**Single Source of Truth:** Jedes Stück lebt komplett in seiner Datei.
Jeder Tag lebt komplett in seinem Logbuch-Eintrag. Kein externer Tracker.

---

## Routing-Tabelle

| Was du gerade tust | Welcher Skill | Lies vorher |
|---|---|---|
| Strand verlassen, schnell festhalten was war | `/feld` | nichts |
| Stück ist geschliffen, bekommt Identität | `/stueck` | `kontext/marke.md` |
| Reisetag soll zu Content werden | `/tag` | `kontext/marke.md`, `kontext/zielgruppe.md` |
| Stück soll in den Shop | `/shop` | `kontext/marke.md`, zugehörige `stuecke/stueck-NNNN.md` |
| Monatsende, Rückblick + Drop-Vorbereitung | `/monat` | letzte 4 Wochen Logbuch + neue Stücke |

---

## Frontmatter-Referenz

### Logbuch-Eintrag (`logbuch/YYYY-MM-DD.md`)
```yaml
type: logbuch
datum: YYYY-MM-DD
ort: "Skagen, DK"
gps: "57.7361, 10.6207"
w3w: "///wort.wort.wort"
wetter: "Wind 6, klar, 9°C"
gefunden: 3              # Anzahl brauchbarer Stücke
stuecke:                 # Verlinkung
  - "[[stueck-0042]]"
  - "[[stueck-0043]]"
stimmung: "ruhig"
notiz_kurz: "erste Eiche seit Tagen"
verarbeitet: false       # true wenn /tag durchlief
```

### Stück (`stuecke/stueck-NNNN.md`)
```yaml
type: stueck
nr: 0042
gefunden_am: YYYY-MM-DD
gefunden_in: "[[YYYY-MM-DD]]"   # Logbuch-Verlinkung
ort: "Skagen Nordstrand, DK"
gps: "57.7361, 10.6207"
w3w: "///wort.wort.wort"
holzart_vermutung: "Eiche"
laenge_cm: 38
durchmesser_cm: 4
zustand: "roh"           # roh | geschliffen | geoelt | fertig | verkauft
geplant_als: "Türgriff"  # Türgriff | Stoßgriff | Möbelgriff | offen
preis_eur: null
shop_listing: ""         # [[outputs/sanity/stueck-0042]]
verkauft_am: null
kund_in: null
fotos:
  - "fund.jpg"
  - "geschliffen.jpg"
```

### Blog-Post (`outputs/blog/YYYY-MM-DD-slug.md`)
```yaml
type: blog
datum: YYYY-MM-DD
slug: ""
titel: ""
zusammenfassung: ""      # max 160 Zeichen, dient auch als Meta-Description
keywords:
  - ""
verlinkt_stuecke:
  - "[[stueck-0042]]"
status: draft            # draft | review | scheduled | published
astro_blog_id: null
url: ""
```

---

## Slash Commands

| Command | Was es tut                                                |
|---|---|
| `/feld` | Roh-Eintrag aus Voice/Notiz → Logbuch                     |
| `/stueck` | Holzstück anlegen oder aktualisieren                      |
| `/tag` | Aus Logbuch + Stücken → Blog + Social + Newsletter-Absatz |
| `/shop` | Stück → Astro-fertige Produktbeschreibung                 |
| `/monat` | Monats-Rückblick, Drop-Vorbereitung                       |

---

## Output-Namenskonvention

```
logbuch/2026-04-29.md
stuecke/stueck-0042.md
outputs/blog/2026-04-29-erste-eiche-seit-tagen.md
outputs/social/2026-04-29-pinterest.md
outputs/social/2026-04-29-instagram.md
outputs/newsletter/woche-17.md
outputs/sanity/stueck-0042.md
```

---

## Was diese Pipeline NICHT ist

- Kein Massenmarkt-System. Eine Marke, ein Vault, fertig.
- Kein Marktschreier-Apparat. Kein Disclaimer-Ballast, keine §-Verweise,
  keine Author-Authority-Checklisten. Das ist Lifestyle, nicht Amazon.
- Kein Auto-Publisher. Du entscheidest, was rausgeht. Pipeline
  produziert Drafts, du klickst veröffentlichen.
- Keine Komplexität um der Komplexität willen. Wenn ein Skill in
  drei Monaten nicht benutzt wurde, fliegt er raus.

---

## Philosophie

Die Reise ist das Produkt. Das Holz ist der Beweis. Die Pipeline ist nur dafür da, dass beides Zeit füreinander hat.

Wenn du am Strand schnorchelst statt am Laptop zu sitzen, hat das System gewonnen. Wenn du am Laptop sitzt statt am Strand zu schnorcheln, ist irgendwo etwas kaputt — wahrscheinlich ein zu komplizierter Skill. Vereinfachen, nicht ausbauen.
