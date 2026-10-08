// Schaufenster: Sucher mit Gegenproben in beide Richtungen.
// Läuft mit `npm test` (Node ≥ 22, keine Abhängigkeiten), im pre-push-Hook und in der Action.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { projekte, quellOrdner, dateienListe, pruefeAlles, pruefeCommit, pruefeCommitAngaben, ROOT, pruefeOrdner, pruefeText, pruefeReadme, wortHash, SPERRLISTE, ERLAUBT } from './pruefen.mjs'

const mitKopie = (quelle, fn) => {
  const kopie = fs.mkdtempSync(path.join(os.tmpdir(), 'schaufenster-'))
  try {
    if (quelle) fs.cpSync(quelle, kopie, { recursive: true })
    return fn(kopie)
  } finally {
    fs.rmSync(kopie, { recursive: true, force: true })
  }
}

test('1 es gibt Projekt-Ordner, und jeder ist nicht leer', () => {
  const ordner = projekte()
  assert.ok(ordner.includes('driftcraft'), `gefunden: ${ordner}`)
  for (const name of ordner) assert.ok(dateienListe(quellOrdner(name)).length >= 2, `${name} fast leer`)
})

test('2 Sucher: das ganze Repo ist sauber', () => {
  const ergebnis = pruefeAlles()
  assert.ok(ergebnis.find((e) => e.name === 'driftcraft').dateien >= 10, 'Sucher hat driftcraft nicht angeschaut')
  assert.deepEqual(ergebnis.flatMap((e) => e.funde), [])
})

test('3 Gegenprobe Sucher: eingeschmuggelte Angaben werden gefunden', () => {
  const liste = new Map([[wortHash('Testvorname'), 'Person'], [wortHash('Bus Modell'), 'Fahrzeug']])
  const arten = (text) => pruefeText(text, 'x.md', ERLAUBT.driftcraft, liste).map((f) => f.art)
  assert.deepEqual(arten('Ein Maker (Testvorname aka. X) zieht los.'), ['Sperrliste: Person'])
  assert.deepEqual(arten('TESTVORNAME'), ['Sperrliste: Person'])
  assert.deepEqual(arten('mit dem bus-modell unterwegs'), ['Sperrliste: Fahrzeug'])
  assert.deepEqual(arten('schreib an jemand@example.org'), ['E-Mail-Adresse'])
  assert.deepEqual(arten('Ruf an: +40 712 345 678'), ['Telefonnummer'])
  assert.deepEqual(arten('Tel. 0171 2345678'), ['Telefonnummer'])
  assert.deepEqual(arten('STRIPE=sk_live_abcdefghijklmnop'), ['Schlüssel'])
  assert.deepEqual(arten('api_key: abcdefgh12345'), ['Schlüssel'])
  assert.deepEqual(arten('x 3f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a y'), ['Schlüssel (lange Zeichenkette)'])
  assert.deepEqual(arten('gps: "48.1374, 11.5755"'), ['Koordinate'])
  assert.deepEqual(arten('gps: N 46.5000°, E 24.4000°'), ['Koordinate'])
  assert.deepEqual(arten('w3w: ///drei.echte.woerter'), ['what3words'])
  assert.deepEqual(arten('Ein Maker (Nicht Kollektiv) aka. Parzival'), ['Name (Parzival)'])
  assert.deepEqual(arten('siehe [[treibholz-shop-projekt]]'), ['Nicht mitgeliefertes Dokument'])
})

test('4 Gegenprobe Sucher: erlaubte Beispiele bleiben grün — aber nur in ihrem Ordner', () => {
  const liste = new Map([[wortHash('Testvorname'), 'Person']])
  const funde = (text, erlaubt = ERLAUBT.driftcraft) => pruefeText(text, 'x.md', erlaubt, liste)
  assert.deepEqual(funde('gps: "57.7361, 10.6207"'), [])
  assert.deepEqual(funde('gps: N 46.511512°, E 24.473579°'), [])
  assert.deepEqual(funde('gps: "N46.482411, E24.425506"'), [])
  assert.deepEqual(funde('w3w: ///wichtigere.einlage.hügelig und ///wort.wort.wort'), [])
  assert.deepEqual(funde('(c) 2026 Kollektiv Parzival 3000, www.parzival-3000.com'), [])
  assert.deepEqual(funde('Lochabstand 192 mm, Format 1000x1500, Nr. 0042, 2026-04-29'), [])
  // Ein anderer Ordner erbt die Ausnahmen nicht.
  assert.deepEqual(funde('gps: N 46.511512°, E 24.473579°', {}).map((f) => f.art), ['Koordinate'])
})

test('5 Gegenprobe Ordner: Binärdatei, fehlende LICENSE, Umlaut-Dateiname', () => {
  mitKopie(null, (dir) => {
    fs.writeFileSync(path.join(dir, 'bild.png'), Buffer.from([0x89, 0x50, 0x4e, 0x47, 0, 0, 0, 0]))
    fs.writeFileSync(path.join(dir, 'Über.md'), 'Text\n')
    assert.deepEqual(pruefeOrdner(dir).map((f) => f.art).sort(), ['Binärdatei', 'Dateiname nicht ASCII', 'Lizenz fehlt'])
    fs.writeFileSync(path.join(dir, 'LICENSE'), 'x\n')
    fs.rmSync(path.join(dir, 'Über.md'))
    const sha = '8f0a4f4a1d0d4b8f' // falscher Hash: bleibt ein Fund
    assert.deepEqual(pruefeOrdner(dir, { binaer: { 'bild.png': sha } }).map((f) => f.art), ['Binärdatei'])
  })
  assert.ok(SPERRLISTE.size >= 4)
})

test('6 Gegenprobe README: fehlender und erfundener Ordner werden gemeldet', () => {
  assert.deepEqual(pruefeReadme('[A](./driftcraft/)', ['driftcraft']), [])
  assert.deepEqual(pruefeReadme('nichts verlinkt', ['driftcraft']).map((f) => f.wert), ['Ordner nicht aufgeführt: driftcraft'])
  assert.deepEqual(pruefeReadme('[A](./driftcraft/) [B](./folgt/)', ['driftcraft']).map((f) => f.wert), ['aufgeführt, aber nicht da: folgt'])
})

test('7 Gegenprobe Gesamtlauf: leeres Repo ist nicht grün', () => {
  mitKopie(null, (root) => {
    const funde = pruefeAlles(root).flatMap((e) => e.funde)
    assert.ok(funde.some((f) => f.art === 'leer'))
  })
})

const NOREPLY = '1+test@users.noreply.github.com'
const TESTLISTE = new Map([[wortHash('Testvorname'), 'Person']])

test('8 Commit-Angaben: Nachricht und E-Mails', () => {
  const ok = { sha: 'abc1234', nachricht: 'Ein Satz\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n', autorName: 'konto', autorMail: NOREPLY, committerName: 'konto', committerMail: NOREPLY }
  assert.deepEqual(pruefeCommitAngaben(ok, TESTLISTE), [])
  assert.deepEqual(pruefeCommitAngaben({ ...ok, nachricht: 'Fix von Testvorname' }, TESTLISTE).map((f) => f.art), ['Sperrliste: Person'])
  assert.deepEqual(pruefeCommitAngaben({ ...ok, autorMail: 'jemand@example.org' }, TESTLISTE).map((f) => f.art), ['Autor-E-Mail'])
  assert.deepEqual(pruefeCommitAngaben({ ...ok, committerMail: '' }, TESTLISTE).map((f) => f.art), ['Committer-E-Mail'])
  assert.deepEqual(pruefeCommitAngaben({ ...ok, autorName: 'Testvorname X' }, TESTLISTE).map((f) => f.art), ['Sperrliste: Person'])
  assert.deepEqual(pruefeCommitAngaben({ ...ok, nachricht: 'Co-Authored-By: X <x@example.org>' }, TESTLISTE).map((f) => f.art), ['E-Mail-Adresse'])
  assert.deepEqual(pruefeCommitAngaben({ ...ok, nachricht: 'This reverts commit 810db2a4163773424620108f75b05c89c005af6f.' }, TESTLISTE), [])
  assert.deepEqual(pruefeCommitAngaben({ ...ok, nachricht: 'token 810db2a4163773424620108f75b05c89c005af6f' }, TESTLISTE).map((f) => f.art), ['Schlüssel (lange Zeichenkette)'])
})

test('9 Commit-Verlauf: entfernter Name bleibt ein Fund im alten Commit', () => {
  mitKopie(null, (repo) => {
    const g = (...a) => execFileSync('git', ['-c', 'user.name=konto', '-c', `user.email=${NOREPLY}`, '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', ...a], { cwd: repo }).toString().trim()
    g('init', '-q', '-b', 'main')
    fs.cpSync(quellOrdner('driftcraft'), path.join(repo, 'driftcraft'), { recursive: true })
    fs.copyFileSync(path.join(ROOT, 'README.md'), path.join(repo, 'README.md'))
    g('add', '-A'); g('commit', '-q', '-m', 'sauber')
    const sauber = g('rev-parse', 'HEAD')
    fs.appendFileSync(path.join(repo, 'driftcraft', 'CLAUDE.md'), '\nTestvorname war hier\n')
    g('commit', '-q', '-am', 'rein')
    const rein = g('rev-parse', 'HEAD')
    g('revert', '--no-edit', 'HEAD')
    const raus = g('rev-parse', 'HEAD')
    assert.deepEqual(pruefeCommit(sauber, repo, TESTLISTE), [])
    assert.deepEqual(pruefeCommit(rein, repo, TESTLISTE).map((f) => f.art), ['Sperrliste: Person'])
    assert.deepEqual(pruefeCommit(raus, repo, TESTLISTE), [])
    // Der Dateistand kommt aus dem Commit, nicht aus dem Arbeitsbaum.
    fs.rmSync(path.join(repo, 'driftcraft', 'LICENSE'))
    assert.deepEqual(pruefeCommit(raus, repo, TESTLISTE), [])
  })
})
