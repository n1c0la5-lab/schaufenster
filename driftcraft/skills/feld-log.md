# Skill: Feld-Log

> Schnelles Aufzeichnen vom Strand. Roh-Eintrag, kein Schliff.
> Das hier soll am Abend am Lagerfeuer auf dem Handy gemacht werden.

---

## Auslöser
`/feld` — Aus rohem Voice-Memo, Notiz oder Stichworten wird ein
Logbuch-Eintrag.

## Kontext laden
Nichts. Bewusst nichts. Schnell sein ist wichtiger als kontextreich.

## Input

Akzeptiere alle Formen:

**A) Strukturiert** (wenn Zeit war):
```
ort: Skagen, DK
gps: 57.7361, 10.6207
wetter: Wind 6, klar, 9°C
gefunden: 3 brauchbare Stücke, eine vermutlich Eiche, gerade
stimmung: ruhig
notiz: erste Eiche seit Tagen
```

**B) Unstrukturiert** (Voice-Memo abgetippt, Notiz, freier Text):
```
"war heute morgen in Skagen am Nordstrand, ziemlich windig, geschätzt
6 Beaufort, 9 Grad ungefähr. drei brauchbare Stücke gefunden, eines
davon ist glaube ich Eiche, schön gerade ungefähr 40cm. Salzkruste hart
wie Beton. erste Eiche seit Tagen, davor nur Kiefer und nutzloses Zeug.
GPS war ungefähr 57.7361, 10.6207. ziemlich glücklich heute abend."
```

**C) Mixed** — Foto-Beschreibung plus Stichworte. Auch okay.

## Ablauf

### 1. Datum bestimmen
Wenn Datum im Input → übernehmen.
Sonst → heutiges Datum (der Eintrag ist meist vom Tag selbst).

### 2. Logbuch-Datei anlegen
Pfad: `logbuch/YYYY-MM-DD.md`

Wenn Datei für diesen Tag schon existiert → erweitern, nicht überschreiben.
Bestehender Eintrag bekommt Trennlinie + neuer Abschnitt.

### 3. Strukturieren
Alles aus dem Input rausholen, aber NICHT erfinden. Wenn ein Feld nicht
genannt wurde, leer lassen. Lieber Lücken als Halluzinationen.

### 4. Frontmatter füllen

```yaml
---
type: logbuch
datum: YYYY-MM-DD
ort: ""                  # Strandname, Land
gps: ""                  # falls vorhanden
w3w: ""                  # what3words, z.B. ///wort.wort.wort
wetter: ""               # falls vorhanden
gefunden: 0              # Anzahl brauchbarer Stücke (Schätzung okay)
stuecke: []              # leer — wird gefüllt wenn /stueck läuft
stimmung: ""             # ein Wort: ruhig, frustriert, kalt, glücklich, müde
notiz_kurz: ""           # max 80 Zeichen, was ist die Headline des Tages
verarbeitet: false
---
```

### 5. Body schreiben
Drei Abschnitte:

```markdown
## Was war

[2-4 Sätze freier Text. Was passierte. Wetter, Strand, Funde,
besondere Beobachtungen. Stimme: erste Person, informell,
kein Marketing-Sprech. Das ist Tagebuch, nicht Blog.]

## Funde

[Bullet-Liste der Stücke, falls genannt. Pro Stück eine Zeile,
egal wie wenig man weiß. Wenn nichts gefunden, einfach „nichts
brauchbares" schreiben.]

- [Holzart-Vermutung] [Maße falls bekannt] — [kurze Beschreibung]
- ...

## Notiz für später

[Was du dem Zukünftigen-Selbst sagen willst. Standorte für nochmal
Hingehen. Werkzeug-Mängel. Ideen für ein bestimmtes Stück. Eine
Zeile reicht. Diese Sektion ist optional.]
```

### 6. Output

```
✓ Logbuch-Eintrag angelegt: logbuch/2026-04-29.md
  Ort: Skagen, DK
  Funde: 3
  Stimmung: ruhig

Nächster Schritt:
  /stueck wenn du ein Stück konkret anlegen willst
  /tag    wenn der Tag in Content verwandelt werden soll
```

## Regeln

- **Niemals erfinden.** Wenn der Input keinen Wetterwert hat, bleibt
  Wetter leer. Niemand wird je „leichte Brise, 14°C" mögen wenn es
  nicht stimmt.
- **Keine Stilisierung.** Das ist ein Logbuch, kein Blog. Stimme darf
  müde, kurz, schlecht gelaunt sein.
- **Schnell sein.** Lieber unvollständig in 30 Sekunden als perfekt
  in 5 Minuten. Der Maker ist gerade am Strand, nicht am Schreibtisch.
- **Keine Bewertung.** Niemand sagt „spannender Tag" außer der Maker
  selbst sagt es. Du wiederholst nur was im Input ist.

## Was dieser Skill NICHT tut

- Keine SEO-Keywords einbauen (kommt in `/tag`)
- Kein Verlinken zu Stücken (kommt in `/stueck` automatisch)
- Kein Erstellen von Social-Drafts (kommt in `/tag`)
- Keine Bilder verarbeiten (Pfade übernehmen, mehr nicht)
