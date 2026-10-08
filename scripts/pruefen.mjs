// Sucher über alle Projekt-Ordner des Schaufensters: Was hier liegt, ist öffentlich.
// Er meldet Personen- und Ortsnamen aus der Sperrliste, E-Mail-Adressen, Telefonnummern,
// Zugangsschlüssel, Koordinaten und what3words-Adressen außerhalb der Erlaubnisliste des Ordners,
// ungeprüfte Binärdateien, Verweise auf nicht mitgelieferte Dokumente, Ordner ohne LICENSE
// und eine README, die andere Ordner auflistet, als es gibt.
//
//   node scripts/pruefen.mjs              → alles prüfen, Exit 1 bei Fund
//   node scripts/pruefen.mjs --hash Wort  → Zeile für die Sperrliste ausgeben
//   node scripts/pruefen.mjs --commit <sha> …  → je Commit Dateistand, Nachricht und E-Mails (pre-push)
//
// Die Sperrliste steht nur als Hash im Repo, damit sie die Namen nicht selbst veröffentlicht.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import os from 'node:os'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
// Projekt = jeder Ordner im Root, außer Werkzeug.
const KEIN_PROJEKT = new Set(['scripts', 'hooks', 'node_modules'])
export function projekte(root = ROOT) {
  return fs.readdirSync(root, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !e.name.startsWith('.') && !KEIN_PROJEKT.has(e.name))
    .map((e) => e.name)
    .sort()
}
export const quellOrdner = (name, root = ROOT) => path.join(root, name)

// Alle Dateien unter dir, als relative Pfade mit '/', sortiert.
export function dateienListe(dir) {
  const out = []
  const lauf = (rel) => {
    for (const e of fs.readdirSync(path.join(dir, rel), { withFileTypes: true })) {
      const r = rel ? `${rel}/${e.name}` : e.name
      if (e.isDirectory()) lauf(r)
      else if (e.isFile()) out.push(r)
      else throw new Error(`Weder Datei noch Ordner (Symlink?): ${r}`)
    }
  }
  lauf('')
  return out.sort()
}

export const normal = (s) => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
export const wortHash = (wort) =>
  crypto.createHash('sha256').update('p3k-pack:' + normal(wort).trim().split(/[^\p{L}\p{N}]+/u).join(' ')).digest('hex').slice(0, 16)

// Einzelwörter oder Wortpaare, verglichen ohne Groß-/Kleinschreibung und ohne Akzente.
export const SPERRLISTE = new Map([
  ['19c6b7d700c64639', 'Person (Vorname)'],
  ['2aa5d22a7e98b5c1', 'Person (Name)'],
  ['e36338374198dd29', 'Person (Name)'],
  ['645b3d7e33fb72e2', 'Fahrzeug'],
])

// Erlaubnisliste pro Projekt-Ordner. Ein Ordner ohne Eintrag hat keine Ausnahmen.
//   koordinaten: Lat/Lon, die stehen bleiben dürfen · w3w: what3words-Adressen
//   binaer: Pfad → sha256 einer von Hand geprüften Binärdatei (Bildinhalt angesehen, Metadaten entfernt)
export const ERLAUBT = {
  driftcraft: {
    // Entscheidung 2026-10-08: die echten Fundorte bleiben als Beispiele stehen.
    koordinaten: [
      { lat: 57.7361, lon: 10.6207, wo: 'Skagen Nordstrand (Beispiel in Vorlagen)' },
      { lat: 46.511512, lon: 24.473579, wo: 'Fundort stueck-0043, Miresch-Ufer bei Cristești' },
      { lat: 46.482411, lon: 24.425506, wo: 'Fundort stueck-0044, Nyarád bei Morești' },
    ],
    w3w: ['///wort.wort.wort', '///wichtigere.einlage.hügelig', '///vertiefen.mögliches.gemustert'],
    binaer: {},
  },
}
const LEER = { koordinaten: [], w3w: [], binaer: {} }

// Der Absender darf vorkommen, eine Person „Parzival“ nicht.
const ERLAUBTE_PHRASEN = [/kollektiv parzival 3000/gi, /parzival-3000\.com/gi]

const MUSTER = [
  ['E-Mail-Adresse', /[\p{L}\p{N}._%+-]+@[\p{L}\p{N}.-]+\.[a-z]{2,}/giu],
  ['Telefonnummer', /(?:\+|\b00)\d{1,3}[\s/-]?\(?\d{1,4}\)?(?:[\s/-]?\d{2,4}){2,}/g],
  ['Telefonnummer', /\b0\d{2,4}[\s/-]\d{3,}(?:[\s/-]\d{2,})?\b/g],
  ['Schlüssel', /\b(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{8,}/g],
  ['Schlüssel', /\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}/g],
  ['Schlüssel', /\bAKIA[0-9A-Z]{16}\b|\bxox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY/g],
  ['Schlüssel', /\b(?:api[_-]?key|secret|token|passw(?:or)?d|passwort)\s*[:=]\s*["']?[^\s"'`]{8,}/gi],
  ['Schlüssel (lange Zeichenkette)', /(?<![\w+=])(?=[\w+=]*\d)(?=[\w+=]*[A-Za-z])[\w+=]{32,}/g],
  ['Schlüssel (JWT)', /\beyJ[\w-]{10,}\.[\w-]{10,}/g],
  ['Name (Parzival)', /parzival/gi],
  ['Konto', /n1c0la5|vision4u/gi],
  ['Nicht mitgeliefertes Dokument', /treibholz-shop-projekt|print-on-demand-erweiterung|adlerhorst/gi],
]

const KOORDINATE = /\b([NS]\s*)?(-?\d{1,2}\.\d{3,})°?\s*,\s*([EWO]\s*)?(-?\d{1,3}\.\d{3,})°?/g
const W3W = /\/\/\/[\p{L}]+\.[\p{L}]+\.[\p{L}]+/gu

const zeileVon = (text, index) => text.slice(0, index).split('\n').length

// Prüft einen Text. sperrliste lässt sich für Tests austauschen.
export function pruefeText(text, datei, erlaubt = LEER, sperrliste = SPERRLISTE) {
  const funde = []
  const fund = (art, index, wert) => funde.push({ datei, zeile: zeileVon(text, index), art, wert })

  let ohneAbsender = text
  for (const p of ERLAUBTE_PHRASEN) ohneAbsender = ohneAbsender.replace(p, (m) => ' '.repeat(m.length))
  for (const [art, re] of MUSTER) for (const m of ohneAbsender.matchAll(re)) fund(art, m.index, m[0])

  for (const m of text.matchAll(KOORDINATE)) {
    const lat = Number(m[2]) * (m[1]?.trim() === 'S' ? -1 : 1)
    const lon = Number(m[4]) * (m[3]?.trim() === 'W' ? -1 : 1)
    const ok = (erlaubt.koordinaten ?? []).some((k) => Math.abs(k.lat - lat) < 1e-4 && Math.abs(k.lon - lon) < 1e-4)
    if (!ok) fund('Koordinate', m.index, m[0])
  }
  for (const m of text.matchAll(W3W)) if (!(erlaubt.w3w ?? []).includes(m[0].toLowerCase())) fund('what3words', m.index, m[0])

  const woerter = [...normal(text).matchAll(/[\p{L}\p{N}]+/gu)]
  for (let i = 0; i < woerter.length; i++) {
    const kandidaten = [woerter[i][0]]
    if (i + 1 < woerter.length) kandidaten.push(`${woerter[i][0]} ${woerter[i + 1][0]}`)
    for (const k of kandidaten) {
      const art = sperrliste.get(wortHash(k))
      if (art) fund(`Sperrliste: ${art}`, woerter[i].index, '(Wort aus der Sperrliste)')
    }
  }
  return funde
}

// Erlaubte Absender in Commits: GitHub-no-reply und der Co-Autor-Vermerk.
const ERLAUBTE_COMMIT_MAIL = /^[^@\s]+@users\.noreply\.github\.com$|^noreply@anthropic\.com$/i
const MAIL_IN_TEXT = /[\p{L}\p{N}._%+-]+@[\p{L}\p{N}.-]+\.[a-z]{2,}/giu

// Reine Prüfung der Commit-Angaben (ohne Dateistand): Nachricht und Autor/Committer.
export function pruefeCommitAngaben({ sha = '', nachricht = '', autorName = '', autorMail = '', committerName = '', committerMail = '' }, sperrliste = SPERRLISTE) {
  const ort = `Commit ${sha.slice(0, 7)}`
  const funde = []
  for (const [rolle, mail] of [['Autor', autorMail], ['Committer', committerMail]])
    if (!/@users\.noreply\.github\.com$/i.test(mail)) funde.push({ datei: ort, zeile: 0, art: `${rolle}-E-Mail`, wert: mail || '(leer)' })
  // Namen: nur die Sperrliste (der Konto-Name selbst ist kein Fund).
  for (const name of [autorName, committerName])
    funde.push(...pruefeText(name, `${ort} (Name)`, LEER, sperrliste).filter((f) => f.art.startsWith('Sperrliste')))
  // Nachricht: alles, außer erlaubten Adressen (Co-Authored-By).
  const ohneErlaubte = nachricht
    .replace(MAIL_IN_TEXT, (m) => (ERLAUBTE_COMMIT_MAIL.test(m) ? ' '.repeat(m.length) : m))
    // Commit-Verweise von git revert / cherry-pick sind keine Schlüssel.
    .replace(/(This reverts commit |cherry picked from commit )[0-9a-f]{40}\b/g, (m, vor) => vor + ' '.repeat(40))
  funde.push(...pruefeText(ohneErlaubte, `${ort} (Nachricht)`, LEER, sperrliste))
  return funde
}

const git = (cwd, args, opts = {}) => execFileSync('git', args, { cwd, maxBuffer: 64 << 20, ...opts })

// Ein Commit vollständig: Angaben plus Dateistand, unabhängig vom Arbeitsbaum.
export function pruefeCommit(sha, repo = ROOT, sperrliste = SPERRLISTE) {
  const [autorName, autorMail, committerName, committerMail, ...rest] = git(repo, ['show', '-s', '--format=%an%x00%ae%x00%cn%x00%ce%x00%B', sha]).toString('utf8').split('\0')
  const funde = pruefeCommitAngaben({ sha, nachricht: rest.join('\0'), autorName, autorMail, committerName, committerMail }, sperrliste)
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'schaufenster-commit-'))
  try {
    const eintraege = git(repo, ['ls-tree', '-r', '-z', sha]).toString('utf8').split('\0').filter(Boolean)
    for (const e of eintraege) {
      const [kopf, rel] = e.split('\t')
      const [modus, typ, objekt] = kopf.split(' ')
      if (typ !== 'blob' || modus === '120000') {
        funde.push({ datei: `Commit ${sha.slice(0, 7)}: ${rel}`, zeile: 0, art: 'kein normales File', wert: `${typ} ${modus}` })
        continue
      }
      const ziel = path.join(tmp, rel)
      fs.mkdirSync(path.dirname(ziel), { recursive: true })
      fs.writeFileSync(ziel, git(repo, ['cat-file', 'blob', objekt]))
    }
    for (const { name, funde: f } of pruefeAlles(tmp, sperrliste))
      for (const x of f) funde.push({ ...x, datei: `Commit ${sha.slice(0, 7)}: ${name === 'README.md' ? '' : name + '/'}${x.datei}` })
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true })
  }
  return funde
}

const istText = (buf) => !buf.includes(0) && Buffer.from(buf.toString('utf8'), 'utf8').equals(buf)

export function pruefeOrdner(dir, erlaubt = LEER, sperrliste = SPERRLISTE) {
  const funde = []
  const dateien = dateienListe(dir)
  if (!dateien.includes('LICENSE')) funde.push({ datei: 'LICENSE', zeile: 0, art: 'Lizenz fehlt', wert: 'jeder Ordner trägt seine eigene LICENSE' })
  for (const rel of dateien) {
    funde.push(...pruefeText(rel, `${rel} (Dateiname)`, erlaubt, sperrliste))
    if (!/^[\x20-\x7e]+$/.test(rel)) funde.push({ datei: rel, zeile: 0, art: 'Dateiname nicht ASCII', wert: 'Umlaute zerlegen manche Entpacker' })
    const buf = fs.readFileSync(path.join(dir, rel))
    if (istText(buf)) funde.push(...pruefeText(buf.toString('utf8'), rel, erlaubt, sperrliste))
    else if ((erlaubt.binaer ?? {})[rel] !== crypto.createHash('sha256').update(buf).digest('hex'))
      funde.push({ datei: rel, zeile: 0, art: 'Binärdatei', wert: 'Inhalt ansehen, Metadaten entfernen, dann sha256 in ERLAUBT.binaer' })
  }
  return funde
}

// Die README listet genau die vorhandenen Projekt-Ordner, als Link „](./name/)“.
export function pruefeReadme(text, ordner) {
  const verlinkt = new Set([...text.matchAll(/\]\(\.\/([^/)]+)\/?\)/g)].map((m) => m[1]))
  const funde = []
  for (const o of ordner) if (!verlinkt.has(o)) funde.push({ datei: 'README.md', zeile: 0, art: 'README', wert: `Ordner nicht aufgeführt: ${o}` })
  for (const v of verlinkt) if (!ordner.includes(v)) funde.push({ datei: 'README.md', zeile: 0, art: 'README', wert: `aufgeführt, aber nicht da: ${v}` })
  return funde
}

export function pruefeAlles(root = ROOT, sperrliste = SPERRLISTE) {
  const ergebnis = []
  const ordner = projekte(root)
  for (const name of ordner) {
    const dir = quellOrdner(name, root)
    ergebnis.push({ name, dateien: dateienListe(dir).length, funde: pruefeOrdner(dir, ERLAUBT[name] ?? LEER, sperrliste) })
  }
  const readme = fs.existsSync(path.join(root, 'README.md')) ? fs.readFileSync(path.join(root, 'README.md'), 'utf8') : ''
  ergebnis.push({ name: 'README.md', dateien: readme ? 1 : 0, funde: [...pruefeText(readme, 'README.md', LEER, sperrliste), ...pruefeReadme(readme, ordner)] })
  if (!ordner.length) ergebnis.push({ name: '(Root)', dateien: 0, funde: [{ datei: '', zeile: 0, art: 'leer', wert: 'kein Projekt-Ordner gefunden' }] })
  return ergebnis
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const c = process.argv.indexOf('--commit')
  if (c > 0) {
    const shas = process.argv.slice(c + 1)
    if (!shas.length) {
      console.error('--commit braucht mindestens einen Commit')
      process.exit(2)
    }
    let summe = 0
    for (const sha of shas) {
      const funde = pruefeCommit(sha, process.cwd())
      console.log(`${sha.slice(0, 7)}: ${funde.length} Funde`)
      for (const f of funde) console.log(`  ${f.datei}:${f.zeile}  ${f.art}  ${f.wert}`)
      summe += funde.length
    }
    process.exit(summe ? 1 : 0)
  }
  const i = process.argv.indexOf('--hash')
  if (i > 0) {
    const wort = process.argv.slice(i + 1).join(' ')
    console.log(`  ['${wortHash(wort)}', '<Art>'],`)
    process.exit(0)
  }
  let summe = 0
  for (const { name, dateien, funde } of pruefeAlles()) {
    console.log(`${name}: ${dateien} Dateien geprüft, ${funde.length} Funde`)
    for (const f of funde) console.log(`  ${f.datei}:${f.zeile}  ${f.art}  ${f.wert}`)
    summe += funde.length
  }
  process.exit(summe ? 1 : 0)
}
