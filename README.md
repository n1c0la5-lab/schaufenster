# Schaufenster

Vorlagen und Werkzeuge vom Kollektiv Parzival 3000 — zum Kopieren, Nachbauen, Weitergeben.
Ein Projekt ist ein Ordner.

## Projekte

| Projekt | Worum es geht | Quest |
|---|---|---|
| [DriftCraft](./driftcraft/) | Obsidian-Vault für eine reisende Treibholz-Marke: Strand → Werkstatt → Netz, mit Skills für Claude Code. | [parzival-3000.com/quests/driftcraft](https://www.parzival-3000.com/quests/driftcraft) |

## Herunterladen

Auf GitHub **Code → Download ZIP** (lädt das ganze Schaufenster), darin den Projekt-Ordner,
z. B. `driftcraft`, als Vault in Obsidian öffnen. Alternativ `git clone`.

## Prüfen

Das Repo ist öffentlich, deshalb prüft ein Hook vor jedem Push. Nach dem Klonen einmal:

```bash
git config core.hooksPath hooks
```

Der Hook `hooks/pre-push` führt `node scripts/pruefen.mjs` und `npm test` aus (Node ≥ 22, keine
Abhängigkeiten) und verweigert den Push bei einem Fund, bei uncommitteten Änderungen oder wenn ein
anderer Stand als HEAD gepusht werden soll. Dieselbe Prüfung läuft danach als GitHub-Action.

Der Sucher meldet Namen aus der Sperrliste, E-Mail-Adressen, Telefonnummern, Schlüssel,
Koordinaten und what3words-Adressen außerhalb der Erlaubnisliste des Ordners, ungeprüfte
Binärdateien, Ordner ohne `LICENSE` und Ordner, die hier nicht aufgeführt sind.
Neues Wort für die Sperrliste: `node scripts/pruefen.mjs --hash "Wort"` und die Zeile in `SPERRLISTE` eintragen.

## Lizenzen

Jeder Ordner trägt seine eigene `LICENSE`:

| Teil | Lizenz |
|---|---|
| `driftcraft/` | CC BY 4.0 |
| Hilfsskripte (`scripts/`, `hooks/`, `.github/`) | MIT (`LICENSE` im Root) |

Rechteinhaber: Kollektiv Parzival 3000. „DriftCraft.eu“ ist im Pack nur ein Beispielname für die eigene Marke.
