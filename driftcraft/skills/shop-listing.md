# Skill: Shop-Listing

> Aus einem fertigen Stück wird eine Sanity-fertige Produktseite.
> Keine direkte API-Anbindung — Output ist Markdown plus Felder zum
> Reinkopieren ins Sanity Studio.

---

## Auslöser
`/shop` — Shop-Listing für ein Stück erstellen.

## Voraussetzung
Stück muss Status `fertig` haben. Wenn nicht — kurzer Hinweis und
Abbruch.

## Kontext laden
- `kontext/marke.md` — Stimme
- `kontext/zielgruppe.md` — wer kauft (ICP 1)
- Das Stück selbst: `stuecke/stueck-NNNN.md`

## Input

```
/shop stueck-0042
preis: 145
```

Optional:
```
/shop stueck-0042
preis: 145
befestigung: M8 Punkthalter (durchgehend)
lochabstand: 192mm
versandgewicht_g: 850
```

## Ablauf

### 1. Stück-Daten laden

Alle Felder aus `stuecke/stueck-NNNN.md` ziehen:
- Holzart, Maße, Fundort, GPS, Datum, Story-Kern
- Fotos (Pfade)
- Werkstatt-Verlauf

Wenn essenzielle Felder fehlen (Holzart, Maße, Story-Kern) → fragen
statt schätzen.

### 2. Listing-Datei erstellen

Pfad: `outputs/sanity/stueck-NNNN.md`

```yaml
---
type: sanity_listing
stueck: "[[stueck-0042]]"
_type: "stueck"                 # Sanity Document Type
title: ""                       # max 70 Zeichen, Suchbegriff vorne
slug: ""                        # url-slug: holzart-typ-ort (lowercase, kebab)
holzart: ""
laenge_cm: 0
durchmesser_cm: 0
gewicht_g: 0
preis_eur: 0
status: "verfuegbar"            # verfuegbar | verkauft
stripe_link: ""                 # manuell nach Stripe-Erstellung eintragen
ort: ""
gps: ""
gefunden_am: ""
fotos: []                       # Dateinamen, Reihenfolge wie in Schritt 6
sanity_doc_id: null             # nach manuellem Upload in Sanity eintragen
---
```

### 3. Title und Slug generieren

Format: `[Holzart] [Typ] · [Ort] · [Maße]`

Beispiele:
- `Eichen-Türgriff · Skagen · 38 cm`
- `Kiefer-Möbelgriff · Algarve · 14 cm`

Regeln:
- Max 70 Zeichen
- Suchbegriff (Holzart + Typ) vorne — Google-Shopping
- Ort dabei — das macht das Stück suchbar und einzigartig
- Maße konkret in cm
- Slug aus Title ableiten: `eichen-tuergriff-skagen-38cm`

### 4. Beschreibung — Drei-Block-Struktur

```markdown
## [Title]

### Story
[2-3 Sätze in Marken-Stimme. Basis: Story-Kern aus dem Stück.
Etwas erweitert um Details aus Logbuch (Wetter, Fund-Situation).
Kein Verkaufs-Sprech, kein "perfekt für ihre Küche".]

### Holz und Maße
- **Holz:** [Eiche, vermutlich — falls unsicher, ehrlich sagen]
- **Länge:** [cm]
- **Durchmesser/Stärke:** [cm]
- **Gewicht (ohne Beschlag):** [g]
- **Behandlung:** [geölt mit Hartwachsöl / unbehandelt / gewachst]
- **Besonderheiten:** [Maserung, Risse, Spuren — alles was sichtbar
  ist und keine Reklamation auslösen darf]

### Befestigung
- **Typ:** [M8 Gewindestange / Punkthalter durchgehend / Rückseiten-Schraube]
- **Lochabstand:** [192 mm / individuell — falls Kund:in etwas wissen muss]
- **Geeignet für:** [Holztür / Glastür / Schubladenfront / Schranktür]
- **Im Lieferumfang:** [Beschlag, Schrauben, Anleitung]

### Fund
- **Strand:** [Skagen Nordstrand, Dänemark]
- **GPS:** [57.7361, 10.6207] — [optional Karten-Link]
- **Gefunden am:** [29. April 2026]
- **Wetter beim Fund:** [optional, falls schöner Detail]

### Versand und Rückgabe
- Versand innerhalb 3-5 Werktagen aus Deutschland
- DHL versichert, Tracking-Link kommt per Mail
- 14 Tage EU-weit Rückgabe ohne Begründung, Rücksendung kostenfrei
- Keine Nachbestellung möglich — Unikat

### Pflege
[2-3 Sätze. Wie pflegen, was vermeiden. Konkret. Beispiel:
"Mit feuchtem Tuch abwischen reicht. Einmal jährlich mit etwas
Hartwachsöl nachbehandeln. Nicht in der Spülmaschine. Nicht
direkt unter der Dunstabzugshaube fettiger Küchen — Holz mag
keine Dauerstrapaze."]
```

### 5. Sanity-Tags generieren

Generiere passende Tags aus den Stück-Daten (werden in Sanity als
String-Array im `tags`-Feld eingetragen):
```yaml
tags:
  - "Holzart:Eiche"
  - "Typ:Türgriff"
  - "Land:Dänemark"
  - "Strand:Skagen"
  - "Drop:2026-Q2"          # Quartal des Verkaufs-Listings
```

### 6. Foto-Empfehlung

```markdown
## Fotos für dieses Listing (in dieser Reihenfolge):

1. [fund.jpg] — Hauptbild: Stück am Strand wo gefunden
2. [werkstatt.jpg] — Beim Schleifen / im Werkprozess
3. [fertig-frei.jpg] — Fertiges Stück, neutraler Hintergrund
4. [fertig-anwendung.jpg] — Montiert oder visualisiert (Tür/Schrank)
5. [detail-maserung.jpg] — Nahaufnahme Holzmaserung
6. [befestigung.jpg] — Beschlag-Set einzeln gezeigt

Falls Bilder fehlen: Vor Listing-Veröffentlichung produzieren.
Mindestens Bilder 1, 3 und 6 sind Pflicht.
```

### 7. Newsletter-Hinweis (optional, wenn Drop)

Wenn das Stück zu einem geplanten Drop gehört:
- Eintrag in nächste Newsletter-Datei mit Vorab-Hinweis
- "Subscriber sehen 24h vor allen anderen" — wichtig für Loyalität

### 8. Aktualisierungen im Stück

Im `stuecke/stueck-NNNN.md`:
```yaml
shop_listing: "[[outputs/sanity/stueck-0042]]"
preis_eur: 145
```

### 9. Output

```
✓ Shop-Listing erstellt: outputs/sanity/stueck-0042.md

Title:    Eichen-Türgriff · Skagen · 38 cm
Slug:     eichen-tuergriff-skagen-38cm
Preis:    145 €
Tags:     5 Tags vorgeschlagen
Bilder:   6 Bilder empfohlen, 3 Pflicht

Vor Upload prüfen:
  ☐ Alle Pflicht-Bilder vorhanden
  ☐ Maße nochmal nachgemessen
  ☐ Befestigungs-Set bereit zum Versand
  ☐ Versandgewicht im Frontmatter eingetragen
  ☐ Stripe Payment Link erstellt und in Frontmatter eingetragen

Manueller Upload: Sanity Studio → neues Dokument (Typ: stueck) →
Felder aus Frontmatter übertragen → Bilder hochladen → Status "verfuegbar".
Nach Upload: sanity_doc_id in diese Datei eintragen.
```

## Regeln

- **Keine Marketing-Übertreibungen.** „Perfekt für jede Küche" ist
  Quatsch. Lieber „Befestigt sich an Standardlochabstand 192 mm,
  passt also auf die meisten IKEA-Fronten der letzten 15 Jahre".
- **Befestigung ist nicht optional.** Wenn unklar ist wie das Stück
  montiert wird, ist es nicht verkaufsbereit. Skill bricht ab.
- **GPS und Fundort sind Marken-Fundament.** Nicht weglassen, auch
  wenn ein Stück unspektakulär aussieht.
- **Pflege-Hinweis ist Kund:innen-Schutz.** Reklamationen aus
  fehlender Pflege wegen fehlender Hinweise sind selbstverschuldet.
- **Preis bestimmt der Maker.** Skill schlägt nichts vor.
- **Stripe-Link vor Upload.** Kein Listing in Sanity ohne fertigen
  Stripe Payment Link — sonst ist das Stück sichtbar aber nicht kaufbar.

## Was dieser Skill NICHT tut

- Keine direkte Sanity-API-Anbindung (bewusst — manueller Schritt
  als Qualitätskontrolle)
- Kein automatisches Erstellen von Stripe Payment Links
- Keine Bildbearbeitung
- Keine Konkurrenzpreise-Recherche
- Keine SEO-Schlüsselwort-Optimierung außerhalb der Marken-Stimme
