# Skill: Monats-Rückblick

> Einmal im Monat. Was war, was wurde fertig, was kommt als Drop in
> den Shop. Pflege-Skill für die Pipeline und Vorbereitung für den
> nächsten großen Newsletter.

---

## Auslöser
`/monat` — Monatsrückblick und Drop-Vorbereitung.

## Kontext laden
- `kontext/marke.md`, `kontext/zielgruppe.md`
- Alle `logbuch/YYYY-MM-*.md` des Monats
- Alle `stuecke/*.md` mit Status-Änderung im Monat
- Bestehende `outputs/blog/*` und `outputs/newsletter/*` des Monats

## Input

```
/monat 2026-04
```

Optional: 
```
/monat 2026-04 mit-drop
```
(falls am Monatsende ein Drop in den Shop geht)

## Ablauf

### 1. Inventur

Für den Monat sammeln:

**Reise:**
- Wie viele Logbuch-Tage
- Welche Orte (Liste, geographisch)
- Welche Länder
- Stimmungs-Verteilung (gute/mittlere/schlechte Tage grob)

**Funde:**
- Anzahl gefundener Stücke
- Anzahl davon brauchbar
- Anzahl jetzt im Status `fertig`

**Werkstatt:**
- Pro Stück: aktueller Status
- Was wurde im Monat fertig

**Verkäufe:**
- Anzahl verkaufter Stücke
- Umsatz EUR
- Wer hat gekauft (anonymisiert: Stadt/Land)

**Content:**
- Anzahl Blog-Posts
- Anzahl Pinterest-Pins
- Anzahl Instagram-Posts
- Anzahl Newsletter

### 2. Rückblick-Datei erzeugen

Pfad: `outputs/newsletter/monatsrueckblick-YYYY-MM.md`

Diese ist gleichzeitig:
- Persönlicher Rückblick (für den Maker selbst)
- Großer Monats-Newsletter (an Subscriber)
- Drop-Ankündigung (falls neue Stücke im Shop landen)

```yaml
---
type: monatsrueckblick
monat: YYYY-MM
status: draft
versand_geplant: YYYY-MM-DD
verlinkt_stuecke:
  - "[[stueck-0042]]"
verlinkt_blog:
  - "[[outputs/blog/...]]"
---

# [Monat YYYY] — [Headline-Ort oder Thema des Monats]

## Wo wir waren
[Kurze Reise-Zusammenfassung. Geographisch, mit Daten.
2-3 Absätze. Konkret. Was war besonders, was war hart.]

## Was wir gefunden haben
[Liste der signifikanten Stücke. Jedes mit 1-2 Sätzen Story.
Bild-Verweise.]

## Was jetzt im Shop ist
[Falls mit-drop: Liste der neuen Listings mit Link.]
[Falls ohne: was auf dem Weg ist, ohne Datum-Versprechen.]

## Was als nächstes kommt
[Wohin geht die Reise im nächsten Monat. Bewusst vage —
Pläne ändern sich, das ist Teil der Reise.]

## Subscriber-Privileg
[Wenn Drop kommt: 24h Vorab-Zugang, vor offizieller Veröffentlichung.
Konkreter Link, konkrete Zeitangabe.]

---
*Aus dem Camper. [Wo zur Zeit der Mail].*
```

### 3. Drop-Liste (wenn `mit-drop`)

Zusätzliche Datei: `outputs/sanity/drop-YYYY-MM.md`

```markdown
# Drop YYYY-MM — Liste

Stücke die in diesem Monat in den Shop gehen:

| Stück | Title | Preis | Listing-Datei |
|---|---|---|---|
| [[stueck-0042]] | Eichen-Türgriff Skagen 38cm | 145 € | [[outputs/sanity/stueck-0042]] |
| [[stueck-0043]] | ... | ... | ... |

## Upload-Reihenfolge
1. Alle Listings als Draft in Sanity Studio anlegen
2. Bilder hochladen, Reihenfolge prüfen
3. Tags und Kollektion zuweisen
4. Subscriber-Vorab-Mail raus (24h vor Live)
5. Listings auf "Active" setzen
6. Pinterest-Pins und Instagram-Posts veröffentlichen
```

### 4. Pipeline-Hygiene

Beim Monats-Rückblick gleich aufräumen:

- Stücke ohne Logbuch-Bezug? Hinweis ausgeben
- Logbuch-Tage ohne Output, mehr als 2 Wochen alt? Anbieten zu archivieren
- Stücke mit Status `fertig` aber kein Listing? Reminder
- Stücke „roh" seit mehr als 3 Monaten? Frage: weiterverarbeiten oder verwerfen?

### 5. Eine ehrliche Frage am Ende

Skill stellt am Schluss diese Frage zurück, vor der Output-Bestätigung:

> Hat sich der Aufwand für die Pipeline diesen Monat gelohnt?
> Wenn nein: was nervt? (Vereinfachen ist besser als ausbauen.)

Antwort optional in `outputs/newsletter/monatsrueckblick-YYYY-MM.md`
unter `## Notizen für mich selbst` (nicht Teil der Newsletter-Mail,
nur internes Frontmatter-Memo).

### 6. Output

```
✓ Monatsrückblick erstellt: outputs/newsletter/monatsrueckblick-2026-04.md

Monat im Überblick:
  Logbuch-Tage:    23
  Orte:            7 Strände, 2 Länder (DK, DE)
  Stücke gefunden: 12, davon 9 brauchbar
  Stücke fertig:   4 (stueck-0040 bis stueck-0043)
  Verkäufe:        3 Stücke, 380 € Umsatz
  Content:         5 Blog-Posts, 12 Pinterest, 8 Instagram, 4 Newsletter

Drop bereit:       4 Stücke ready für Shop-Upload
                   → outputs/sanity/drop-2026-04.md

Pipeline-Hygiene:
  ⚠ stueck-0035 seit 3 Monaten "roh" — verwerfen oder fertigmachen?
  ⚠ logbuch/2026-04-12.md ohne Output — bewusst übersprungen?

Nächste Schritte:
  1. Newsletter durchlesen, persönliche Note ergänzen
  2. Drop-Liste mit Maker-Auge prüfen, ggf. Reihenfolge ändern
  3. Pipeline-Hygiene-Punkte adressieren
```

## Regeln

- **Inventur ehrlich.** Wenn der Monat dünn war, war er dünn. Kein
  Hochrechnen, kein Schönreden.
- **Drop nur wenn echt fertig.** Nicht „dieser Monat braucht einen
  Drop" — der Drop kommt, wenn Stücke fertig sind, nicht wenn der
  Kalender es will.
- **Subscriber-Privileg ernst nehmen.** Wenn 24h Vorab versprochen,
  dann auch 24h Vorab. Sonst nervt es.
- **Hygiene aktiv ansprechen.** Pipeline-Verschmutzung schleicht
  sich ein. Einmal im Monat aufräumen ist Pflicht.

## Was dieser Skill NICHT tut

- Kein Performance-Tracking (Klicks, Conversions). Wer das will,
  baut es separat — gehört nicht in eine Lifestyle-Pipeline.
- Kein automatischer Versand. Die Newsletter-Mail wird von Hand
  in Mailtool kopiert (z.B. Buttondown, Beehiiv, ConvertKit).
- Keine Buchhaltung. Verkäufe werden für den Rückblick aggregiert,
  nicht für die Steuer. Steuer macht Steuerberater:in.
