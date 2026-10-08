# Skill: Stück-Story

> Aus einem Holzstück wird eine Identität. Mit Nummer, Story, Status,
> Werkstattprozess. Das ist die Karteikarte des Stücks von Fund bis
> Verkauf.

---

## Auslöser
`/stueck` — Stück anlegen oder aktualisieren.

## Kontext laden
- `kontext/marke.md` — Stimme, verbotene Wörter

## Wann den Skill nutzen

Drei typische Momente:

1. **Bei Fund:** Stück hat eine Nummer, ein Foto, einen Logbuch-Bezug.
   Status: `roh`.
2. **Nach Werkstattschritt:** Status-Update („geschliffen", „geölt",
   „fertig"), neue Fotos.
3. **Bei Verkauf:** Status `verkauft`, Käufer:in, Datum.

## Input

**A) Neues Stück:**
```
neu
ort: Skagen Nordstrand, DK
gps: 57.7361, 10.6207
gefunden_am: 2026-04-29
holzart: Eiche (vermutlich)
laenge_cm: 38
durchmesser_cm: 4
foto: fund.jpg
geplant_als: Türgriff
notiz: Salzkruste hart, schöne Maserung erkennbar, kleine Delle in der Mitte
```

**B) Update:**
```
update stueck-0042
status: geschliffen
foto: geschliffen.jpg
notiz: Delle bleibt, Ölung nächste Woche
```

**C) Verkauf:**
```
verkauft stueck-0042
am: 2026-05-15
preis: 145
kund_in: K. M. (Hamburg)
```

## Ablauf

### 1. Stück-Nummer bestimmen

Bei „neu":
- Schau in `stuecke/` was die höchste Nummer ist
- Nimm nächste freie Nummer, vierstellig (`stueck-0042`)
- Stücke werden NICHT recycelt — verkaufte bleiben als Datei
  (Portfolio + Story-Asset)

Bei „update" oder „verkauft":
- Datei `stuecke/stueck-NNNN.md` öffnen
- Felder gezielt aktualisieren, Rest unverändert lassen

### 2. Verlinkung zum Logbuch

Wenn `gefunden_am` gesetzt ist:
- Prüfen ob `logbuch/YYYY-MM-DD.md` existiert
- Falls ja: in dessen Frontmatter `stuecke:` Liste das neue Stück
  einfügen (`- "[[stueck-0042]]"`)
- Falls nein: Hinweis „kein Logbuch-Eintrag für diesen Tag —
  /feld zuerst nutzen?"

### 3. Frontmatter (Neuanlage)

```yaml
---
type: stueck
nr: 0042
gefunden_am: YYYY-MM-DD
gefunden_in: "[[YYYY-MM-DD]]"
ort: ""
gps: ""
w3w: ""                  # what3words, z.B. ///wort.wort.wort
holzart_vermutung: ""
laenge_cm: 0
durchmesser_cm: 0
zustand: "roh"            # roh | geschliffen | geoelt | fertig | verkauft
geplant_als: ""           # Türgriff | Stoßgriff | Möbelgriff | offen
preis_eur: null
shop_listing: ""
verkauft_am: null
kund_in: null
fotos:
  - ""
notizen_intern: ""        # nicht für Kund:innen
story_kern: ""            # 1-2 Sätze, basis für Shop-Listing
---
```

### 4. Body-Struktur

```markdown
# Stück 0042

## Fund
- Ort: [Strand, Land]
- GPS: [Koordinaten]
- Datum: [Tag]
- Logbuch: [[YYYY-MM-DD]]

## Holz
- Vermutung: [Eiche / Kiefer / Buche / unbekannt]
- Maße: L [cm] × Ø [cm]
- Besonderheiten: [Maserung, Risse, Spuren, was auffällt]

## Werkstatt
- [YYYY-MM-DD] Roh, gewaschen
- [YYYY-MM-DD] geschliffen, Korn 80→120→240
- [YYYY-MM-DD] Hartwachsöl, erste Schicht
- ...

## Story-Kern
[1-2 Sätze in Marken-Stimme. Diese Sätze landen später leicht
abgewandelt im Shop-Listing. Konkret, ehrlich, keine Floskeln.
Beispiel: "Eiche, gefunden bei Skagen Anfang April. Salzkruste
war so hart dass die Bürste vor dem Schleifpapier dran musste.
Die kleine Delle in der Mitte bleibt — die war schon da."]

## Geplant als
[Türgriff / Stoßgriff / Möbelgriff / offen]
[Maßangaben, Lochabstand falls vorgesehen]

## Verkauf
[Wird später ausgefüllt]
- Status: [aktiv|verkauft]
- Preis: [EUR]
- Verkauft am: [Datum]
- An: [Initialen + Stadt — keine vollen Namen, DSGVO]
- Shop-Listing: [[outputs/shopify/stueck-0042]]

## Notizen intern
[Alles was nicht in den Shop gehört: Bedenken, Werkstatt-Probleme,
Erinnerungen für nächstes Mal]
```

### 5. Story-Kern generieren

Wichtigster Abschnitt für die Marke. Regeln:

- 1-2 Sätze, max 35 Wörter
- Stimme aus `kontext/marke.md`
- Verwendet konkrete Details aus dem Input (Ort, Wetter, Zustand)
- Keines der verbotenen Wörter
- Wenn Input zu wenig hergibt: ehrlich sein und kürzer schreiben
  statt zu erfinden

### 6. Output

```
✓ Stück angelegt: stuecke/stueck-0042.md
  Holz: Eiche (vermutlich), 38 cm
  Status: roh
  Logbuch verlinkt: 2026-04-29

Story-Kern:
  "Eiche, 38 cm, gefunden bei Skagen Anfang April zwischen Algen.
   Die kleine Delle in der Mitte war schon da."

Nächste Schritte:
  /shop wenn Stück fertig ist und in den Shop soll
  Foto noch fehlt? In Frontmatter `fotos:` ergänzen.
```

## Regeln

- **Holzart-Vermutung statt Behauptung.** „Eiche (vermutlich)" oder
  „Eiche oder Esche" sind ehrlicher als feste Aussage. Niemand wird
  ein Holz-Gutachten verlangen, aber wir lügen nicht.
- **Maße sind verbindlich.** Wenn die Längenangabe später nicht stimmt,
  beschwert sich die Kund:in zurecht. Lieber nochmal messen als raten.
- **Story-Kern ist Marken-Stimme.** Keine Esoterik, keine Superlative,
  keine „magischen Geschichten des Meeres".
- **Verkaufte Stücke werden NICHT gelöscht.** Sie sind Portfolio
  und Beweis dass die Marke real ist.

## Was dieser Skill NICHT tut

- Kein Shopify-Upload (kommt in `/shop`)
- Kein Foto-Bearbeiten
- Keine Preisempfehlung — den Preis setzt der Maker selbst
