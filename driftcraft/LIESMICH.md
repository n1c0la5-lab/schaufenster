# DriftCraft Starter-Pack — LIESMICH

> **PLATZHALTER.** Diese Datei ist nur die technische Kurzanleitung.
> Die eigentliche Geschichte der Pipeline (Strand → Werkstatt → Netz) folgt.

Ein Obsidian-Vault zum Kopieren: die Content-Pipeline einer reisenden
Treibholz-Marke. „DriftCraft.eu“ ist ein **Beispielname** — setz deinen eigenen ein.
Die Fundorte, Logbuch-Einträge und Stücke sind Beispiele aus der Praxis.

## So holst du es

1. Auf GitHub **Code → Download ZIP** (lädt das ganze Schaufenster) und entpacken,
   oder `git clone` des Repos.
2. In Obsidian: *Ordner als Vault öffnen* → den Ordner `driftcraft` wählen.

## Ordner

| Ordner / Datei | Inhalt |
|---|---|
| `CLAUDE.md` | Beschreibung der Pipeline, Frontmatter-Referenz, Routing |
| `ERSTE-SCHRITTE.md` | Was du als Erstes anpassen solltest |
| `kontext/` | Marke, Zielgruppe, Sammelregeln pro Land |
| `skills/` | Die fünf Arbeitsschritte als Anleitungen für Claude |
| `logbuch/` | Ein Eintrag pro Strand-Tag |
| `stuecke/` | Eine Datei pro Holzstück |
| `outputs/` | Was die Pipeline erzeugt (Blog, Social, Newsletter, Shop) |

## Skills mit Claude Code nutzen

1. Im Vault-Ordner `claude` starten. Claude Code liest `CLAUDE.md` automatisch.
2. Einen Skill aufrufen, indem du die Datei nennst, z. B.:
   „Lies `skills/feld-log.md` und leg daraus einen Logbuch-Eintrag an: …“
3. Wer echte Slash-Commands (`/feld`, `/stueck`, `/tag`, `/shop`, `/monat`) möchte,
   kopiert die Skill-Dateien nach `.claude/commands/` und benennt sie
   entsprechend um (`feld.md`, `stueck.md`, `tag.md`, `shop.md`, `monat.md`).

Die Pipeline erzeugt nur Entwürfe. Was veröffentlicht wird, entscheidest du.

## Lizenz

CC BY 4.0 — siehe `LICENSE`. Kollektiv Parzival 3000, parzival-3000.com.
