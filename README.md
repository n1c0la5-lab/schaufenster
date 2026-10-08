# Schaufenster

Vorlagen und Werkzeuge vom Kollektiv Parzival 3000 — zum Kopieren, Nachbauen, Weitergeben.
Ein Projekt ist ein Ordner. Jeder Ordner lässt sich einzeln als ZIP herunterladen (siehe *Releases*).

## Projekte

| Projekt | Worum es geht | Quest |
|---|---|---|
| [DriftCraft](./driftcraft/) | Obsidian-Vault für eine reisende Treibholz-Marke: Strand → Werkstatt → Netz, mit Skills für Claude Code. | [parzival-3000.com/quests/driftcraft](https://www.parzival-3000.com/quests/driftcraft) |

## Herunterladen

Jedes Release enthält pro Ordner eine ZIP (`<ordner>.zip`). Lokal bauen:

```bash
node scripts/zip.mjs            # alle Ordner → dist/<ordner>.zip
node scripts/zip.mjs driftcraft # nur einer
```

## Prüfen

```bash
npm test              # Sucher + ZIP-Rücklesetest + Gegenproben (Node ≥ 22, keine Abhängigkeiten)
node scripts/pruefen.mjs
```

Der Sucher meldet Namen aus der Sperrliste, E-Mail-Adressen, Telefonnummern, Schlüssel,
Koordinaten und what3words-Adressen außerhalb der Erlaubnisliste des Ordners, ungeprüfte
Binärdateien und Ordner ohne `LICENSE`. Neues Wort für die Sperrliste:
`node scripts/pruefen.mjs --hash "Wort"` und die Zeile in `SPERRLISTE` eintragen.

## Lizenzen

Jeder Ordner trägt seine eigene `LICENSE`:

| Teil | Lizenz |
|---|---|
| `driftcraft/` | CC BY 4.0 |
| Hilfsskripte (`scripts/`, `.github/`) | MIT (`LICENSE` im Root) |

Rechteinhaber: Kollektiv Parzival 3000. „DriftCraft.eu“ ist im Pack nur ein Beispielname für die eigene Marke.
