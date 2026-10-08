# Skill: Reise-Tag

> Aus einem Logbuch-Eintrag (plus optional neue Stücke) werden vier
> Outputs: Blog-Post, Pinterest-Pin-Text, Instagram-Caption,
> Newsletter-Absatz. Eine Eingabe, vier Kanäle.

---

## Auslöser
`/tag` — Tag in Content verwandeln.

## Kontext laden
- `kontext/marke.md` — Stimme, verbotene Wörter
- `kontext/zielgruppe.md` — wer liest was, in welchem Format
- Logbuch-Eintrag des Tages
- Falls Stücke im Logbuch verlinkt: alle zugehörigen `stuecke/*.md`

## Input

**A) Standard:**
```
/tag 2026-04-29
```
Greift auf `logbuch/2026-04-29.md` zu, liest verlinkte Stücke mit.

**B) Mit Fokus:**
```
/tag 2026-04-29 fokus: stueck-0042
```
Nutzt den Tag, aber stellt das Stück in den Mittelpunkt.

**C) Mehrtages-Bündel:**
```
/tag 2026-04-25..2026-04-29
```
Aus 5 Tagen wird ein Wochen-Post. Selten nötig.

## Ablauf

### 1. Vorab-Check

- Logbuch existiert? Wenn nein → Abbruch mit Hinweis „/feld zuerst".
- Logbuch ist substantiell? Wenn der Eintrag nur „nichts gefunden,
  miese Stimmung" ist, frage zurück: „Tag war wenig — soll ich
  trotzdem Content produzieren oder lieber überspringen?"
  Schlechte Tage müssen nicht jeden zum Content werden.

### 2. Material einsammeln

Aus Logbuch ziehen:
- Ort, GPS, Wetter
- Was passierte (`## Was war`)
- Funde
- Stimmung
- Notizen

Aus verlinkten Stücken ziehen:
- Holzart, Maße
- Story-Kern
- Aktueller Status (roh, geschliffen, fertig)

### 3. Vier Outputs generieren

Jeden in eigene Datei. Einer nach dem anderen, in dieser Reihenfolge:

#### A) Blog-Post (`outputs/blog/YYYY-MM-DD-{slug}.md`)

```yaml
---
type: blog
datum: YYYY-MM-DD
slug: ""                    # aus Headline ableiten, kebab-case
titel: ""                   # max 65 Zeichen
zusammenfassung: ""         # max 160 Zeichen, dient als Meta-Description
keywords:
  - ""                      # 2-4 organisch passende Begriffe
verlinkt_stuecke:
  - "[[stueck-NNNN]]"
status: draft
---

# [Titel]

[Erster Absatz: Hook. Konkret in den Tag rein. Ort, Wetter, ein Bild
das man sofort sieht. Kein „heute möchte ich euch von..." Einleiten.]

[Zweiter Absatz: Was passierte. 3-5 Sätze. Details aus dem Logbuch.]

[Dritter Absatz: Funde. Wenn ein Stück besonders war — beschreiben.
Verlinkung als Markdown-Link auf das Stück.]

[Vierter Absatz: Was es bedeutet oder was als nächstes kommt. Eine
Reflexion, kein Marketing-CTA.]
```

**Länge:** 250-450 Wörter. Kein Roman.
**Stimme:** Erste Person, informell, ehrlich.
**SEO:** Keywords aus Marken-Vokabular natürlich einbauen
("Treibholz", Ort, Holzart). Kein Stuffing.

#### B) Pinterest-Pin (`outputs/social/YYYY-MM-DD-pinterest.md`)

```markdown
---
type: pinterest
datum: YYYY-MM-DD
zielgruppe: "ICP 1 (Renoviererin) + ICP 2 (Vanlife)"
formate: ["1000x1500"]
---

## Pin 1 — Vertikal, Foto-fokussiert

**Bild:** [Vorschlag aus den Fotos im Logbuch oder Stück]
**Text-Overlay (optional):** "Treibholz finden in Skagen, DK"

**Pin-Titel:** [max 100 Zeichen, deskriptiv und suchbar]
Beispiel: "Treibholz-Türgriff Eiche aus Skagen, Dänemark"

**Pin-Beschreibung:** [max 500 Zeichen, mit Hashtags am Ende]
[2-3 Sätze über das Stück und den Fund. Konkret. Kein "magisch".
Hashtags: #treibholz #driftwood #naturmöbel #handgemacht
#nordseeküste — was passt, max 5]

**Link:** [URL zum Blog-Post oder Shop-Listing]

## Pin 2 (optional) — Reise-fokussiert

[Wenn der Tag viel Reise-Stoff hatte: zweiter Pin der die Reise
betont, weniger das Produkt]
```

#### C) Instagram-Caption (`outputs/social/YYYY-MM-DD-instagram.md`)

```markdown
---
type: instagram
datum: YYYY-MM-DD
format: "Post 4:5"   # oder "Reel 9:16" oder "Carousel"
---

## Caption

[Erste Zeile: Hook. Macht der Algorithmus auf, das Stop-Scrollen.]

[2-4 Zeilen: Was war heute. Konkrete Details, kein Hochglanz.]

[Optional: Eine Frage am Ende oder ein offener Gedanke.]

---
[Hashtags am Ende, getrennt durch Leerzeile. Mix aus:
- Marke (#strandgut o.ä.) — 1
- Nische groß (#driftwood #treibholz) — 2-3
- Nische mittel (#nordseeküste #vanlifecraft) — 3-4
- Nische klein (#skagen #handcraft) — 2-3
Insgesamt 8-12 Hashtags reichen.]
```

#### D) Newsletter-Absatz (`outputs/newsletter/woche-NN.md`)

Wichtig: Newsletter wird wöchentlich. Dieser Skill hängt nur
einen ABSCHNITT in die Datei der aktuellen Woche an, schreibt
nicht die ganze Mail.

```markdown
---
type: newsletter
woche: NN-YYYY            # ISO-Wochennummer
status: draft
versand_geplant: YYYY-MM-DD
---

# Woche NN — [Titel der Woche, später]

[ggf. existierender Inhalt der Woche]

---

## [Datum] — [Ort, Land]

[3-5 Sätze. Wie ein Brief an Freund:innen. Kein Verkaufs-Push.
Konkrete Beobachtung, optional ein Foto-Hinweis. Wenn ein neues
Stück fertig ist: kurze Erwähnung mit Link, aber nicht aufdringlich.]

[Optional: ein Detail das nur Newsletter-Subscriber bekommen —
GPS, Hintergrund, was im Blog nicht steht.]
```

### 4. Status setzen

In Logbuch-Datei:
```yaml
verarbeitet: true
verarbeitet_am: YYYY-MM-DD
outputs:
  - "[[outputs/blog/YYYY-MM-DD-slug]]"
  - "[[outputs/social/YYYY-MM-DD-pinterest]]"
  - "[[outputs/social/YYYY-MM-DD-instagram]]"
  - "[[outputs/newsletter/woche-NN]]"
```

### 5. Output

```
✓ 4 Drafts erzeugt aus logbuch/2026-04-29.md:

  Blog       → outputs/blog/2026-04-29-erste-eiche-seit-tagen.md   (380 Wörter)
  Pinterest  → outputs/social/2026-04-29-pinterest.md              (1 Pin)
  Instagram  → outputs/social/2026-04-29-instagram.md              (Post 4:5)
  Newsletter → outputs/newsletter/woche-17.md                      (Absatz angefügt)

Status: alles draft. Vor Veröffentlichung selbst durchlesen.

Verlinkte Stücke: stueck-0042
```

## Regeln

- **Vier verschiedene Texte.** Nicht der gleiche Text in vier
  Längen. Pinterest ist suchend. Instagram ist scrollend. Blog
  ist lesend. Newsletter ist intim. Ton anpassen.
- **Stimme aus `marke.md` strikt.** Keine verbotenen Wörter.
  Lieber kürzer als floskelig.
- **Nichts erfinden.** Wenn das Logbuch leer ist, ist der Output
  leer. Keine kompensatorische Story-Erfindung.
- **Bilder als Vorschlag, nicht als Befehl.** Skill schlägt vor,
  welches Foto wo passt. Maker entscheidet final.
- **Schlechte Tage dürfen schlechte Tage sein.** Nicht jeder Tag
  muss zu Content werden. Wenn der Skill bei der Vorab-Prüfung
  merkt es ist zu dünn, lieber abbrechen.

## Was dieser Skill NICHT tut

- Kein Auto-Posting auf Pinterest, Instagram, Newsletter-Tool.
  Maker kopiert manuell — Bewusstsein vor Automation.
- Kein astro.build-Update — das ist `/shop`.
- Keine SEO-Audits — wir machen Lifestyle, nicht YMYL.
