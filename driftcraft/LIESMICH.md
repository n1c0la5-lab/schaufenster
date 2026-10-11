# DriftCraft Starter-Pack

> Ein Plan, so klein, dass man morgen damit anfangen kann. Die Zahlen rechnet, wer ihn nachbaut.

## Ausgangslage

Wer unterwegs leben will, fragt zuerst, wovon. Die übliche Antwort ist ein Laptop und ein Kunde, der woanders sitzt. Diese Karte zeigt einen anderen Weg: ein Handwerk, das mitreist, und ein Material, das am Weg liegt.

## Die Idee

Treibholz sammeln, an Flüssen und an Küsten. Daraus Griffe und Beschläge machen, keine Möbel. Die Stücke einzeln im Netz verkaufen, jedes mit Fundort, Datum und Foto.

Das Wasser hat das Holz schon geformt. Die Arbeit besteht darin, zu sehen, was es werden kann.

## Das Produkt

Türgriffe, Schubladengriffe, Knäufe. Befestigt wird nach Norm, damit jeder sie selbst montieren kann. Es gibt keine Serien und keine Nachbestellung. Was verkauft ist, ist weg.

## Die Käufer

Menschen, die gerade eine Küche, ein Bad oder einen Altbau renovieren und wissen, was ein Designerknauf kostet. Sie wollen sehen, wie das Stück montiert aussieht, und eine Geschichte, die sie weitererzählen können. Später kommen Hotels und Architekturbüros dazu, die zwanzig Griffe auf einmal brauchen.

## Der Ablauf: Strand, Werkstatt, Netz

Die Arbeit hat drei Stationen, und dieser Obsidian-Vault folgt ihnen.

**Strand.** Am Abend ein Eintrag: Sprachnotiz, Foto, Ort, Wetter, die Funde des Tages. Mehr nicht.
`/feld` → `logbuch/`

**Werkstatt.** Jedes brauchbare Stück bekommt eine eigene Datei mit Holzart und Maßen und durchläuft die Zustände roh, geschliffen, geölt, fertig und verkauft.
`/stueck` → `stuecke/`

**Netz.** Aus Logbuch und Stücken werden Entwürfe: ein Text für den Blog, einer für Bilder, ein Absatz für den Newsletter, eine Beschreibung für den Shop.
`/tag`, `/shop`, `/monat` → `outputs/`

Aus einem Eintrag am Abend wird alles, was der Shop braucht. Veröffentlicht wird nichts automatisch. Die Pipeline schreibt Entwürfe, und was hinausgeht, entscheidet ein Mensch.

Es gibt keinen Tracker, keine Datenbank und kein Abo. Was zu einem Stück gehört, steht in seiner Datei.

## Der Laden

Statt eines Shopsystems gibt es eine Galerie mit einem Zahlungslink pro Stück. Nach dem Kauf springt der Status auf verkauft. Warenkorb, Varianten und Lager fallen weg, und fast alles läuft im kostenlosen Tarif. Der Bauplan steht in `kontext/treibholz-shop-projekt.md`.

## Die Anmeldung

Als Einzelunternehmer in Georgien mit Kunsthandwerk und Onlinehandel. Den Small Business Status beantragt man vor dem ersten Verkauf. Die Mehrwertsteuer beim Verkauf in die EU und die Zollpapiere sind Fragen für einen Steuerberater, nicht für ein Forum. Die Einzelheiten stehen ebenfalls in `kontext/treibholz-shop-projekt.md`.

## Was offen bleibt

Route, Tempo, Preise, Einnahmen: Das hängt davon ab, wer es macht, und diese Karte rechnet es nicht vor.

Die Beispiele im Obsidian-Vault, also Logbuch, Stücke und zwei Fundorte, stammen aus der Praxis. Sie zeigen, wie ein Eintrag aussieht, nicht, wie viel er einbringt.

## Der Name

DriftCraft.eu steht hier als Beispielname. Die Domain gibt es wirklich, und sie wartet noch auf ihre Reise. Wer aus diesem Plan eine macht, kann sich melden, per Mail an parzival3000@proton.me oder per Direktnachricht auf Instagram an [@parzival.3000](https://www.instagram.com/parzival.3000/). Über einen Ausgleich lässt sich reden.

## Der Maßstab

Wenn du am Strand bist statt am Laptop, hat das System gewonnen. Wenn du am Laptop sitzt statt am Strand, ist irgendwo ein Schritt zu kompliziert geworden. Dann wird vereinfacht, nicht ausgebaut.

---

## So holst du es

1. Auf GitHub **Code → Download ZIP** (lädt das ganze Schaufenster) und entpacken,
   oder `git clone` des Repos.
2. In Obsidian: *Ordner als Vault öffnen* → den Ordner `driftcraft` wählen.

Danach `ERSTE-SCHRITTE.md` lesen. Wer mit Claude Code arbeitet, startet `claude` im Ordner `driftcraft`, dann wird `CLAUDE.md` automatisch gelesen. Wer echte Slash-Commands möchte, kopiert die Dateien aus `skills/` nach `.claude/commands/` und benennt sie nach dem Befehl um (`feld.md`, `stueck.md`, `tag.md`, `shop.md`, `monat.md`).

## Lizenz

CC BY 4.0, siehe `LICENSE`. Kollektiv Parzival 3000, parzival-3000.com.
