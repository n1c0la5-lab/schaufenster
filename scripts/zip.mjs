// Baut die Download-ZIP eines Projekt-Ordners: <ordner>/ → dist/<ordner>.zip (dist/ ist nicht eingecheckt).
// Ohne Abhängigkeiten (nur node:zlib). Dasselbe Skript läuft lokal und in der Release-Action.
//
//   node scripts/zip.mjs              → alle Projekt-Ordner
//   node scripts/zip.mjs driftcraft   → nur diesen
import fs from 'node:fs'
import path from 'node:path'
import zlib from 'node:zlib'
import { fileURLToPath } from 'node:url'

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
// Projekt = jeder Ordner im Root, außer Werkzeug und Ausgabe.
const KEIN_PROJEKT = new Set(['scripts', 'dist', 'node_modules'])
export function projekte(root = ROOT) {
  return fs.readdirSync(root, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !e.name.startsWith('.') && !KEIN_PROJEKT.has(e.name))
    .map((e) => e.name)
    .sort()
}
export const quellOrdner = (name, root = ROOT) => path.join(root, name)
export const zipPfad = (name, root = ROOT) => path.join(root, 'dist', `${name}.zip`)

// Alle Dateien unter dir, als relative Pfade mit '/', sortiert. Leere Ordner kennt Git nicht, die ZIP auch nicht.
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

const CRC_TABELLE = Array.from({ length: 256 }, (_, n) => {
  let c = n
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
  return c >>> 0
})
export function crc32(buf) {
  let c = 0xffffffff
  for (const b of buf) c = CRC_TABELLE[(c ^ b) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}

// Feste Zeit (1980-01-01 00:00) und sortierte Reihenfolge: gleiche Quelle → gleiche Einträge.
const DOS_ZEIT = 0
const DOS_DATUM = (0 << 9) | (1 << 5) | 1
const UTF8 = 0x0800

export function zipBauen(dir, praefix) {
  const lokal = []
  const zentral = []
  let offset = 0
  for (const rel of dateienListe(dir)) {
    const name = Buffer.from(`${praefix}/${rel}`, 'utf8')
    const daten = fs.readFileSync(path.join(dir, rel))
    const gepackt = zlib.deflateRawSync(daten, { level: 9 })
    const crc = crc32(daten)
    const kopf = Buffer.alloc(30)
    kopf.writeUInt32LE(0x04034b50, 0)
    kopf.writeUInt16LE(20, 4)
    kopf.writeUInt16LE(UTF8, 6)
    kopf.writeUInt16LE(8, 8)
    kopf.writeUInt16LE(DOS_ZEIT, 10)
    kopf.writeUInt16LE(DOS_DATUM, 12)
    kopf.writeUInt32LE(crc, 14)
    kopf.writeUInt32LE(gepackt.length, 18)
    kopf.writeUInt32LE(daten.length, 22)
    kopf.writeUInt16LE(name.length, 26)
    kopf.writeUInt16LE(0, 28)
    lokal.push(kopf, name, gepackt)
    const z = Buffer.alloc(46)
    z.writeUInt32LE(0x02014b50, 0)
    z.writeUInt16LE((3 << 8) | 20, 4) // erstellt unter Unix, damit Entpacker die Rechte setzen
    z.writeUInt16LE(20, 6)
    z.writeUInt16LE(UTF8, 8)
    z.writeUInt16LE(8, 10)
    z.writeUInt16LE(DOS_ZEIT, 12)
    z.writeUInt16LE(DOS_DATUM, 14)
    z.writeUInt32LE(crc, 16)
    z.writeUInt32LE(gepackt.length, 20)
    z.writeUInt32LE(daten.length, 24)
    z.writeUInt16LE(name.length, 28)
    z.writeUInt32LE(0, 30) // Extra- und Kommentarlänge
    z.writeUInt32LE(0, 34) // Disk-Nr. + interne Attribute
    z.writeUInt32LE((0o100644 << 16) >>> 0, 38) // externe Attribute: normale Datei, rw-r--r--
    z.writeUInt32LE(offset, 42)
    zentral.push(z, name)
    offset += kopf.length + name.length + gepackt.length
  }
  const zBuf = Buffer.concat(zentral)
  const ende = Buffer.alloc(22)
  ende.writeUInt32LE(0x06054b50, 0)
  ende.writeUInt16LE(zentral.length / 2, 8)
  ende.writeUInt16LE(zentral.length / 2, 10)
  ende.writeUInt32LE(zBuf.length, 12)
  ende.writeUInt32LE(offset, 16)
  return Buffer.concat([...lokal, zBuf, ende])
}

// Liest eine ZIP über das zentrale Verzeichnis zurück: Map Name → Inhalt. Prüft dabei jede CRC.
export function zipLesen(buf) {
  const eocd = buf.lastIndexOf(Buffer.from([0x50, 0x4b, 0x05, 0x06]))
  if (eocd < 0) throw new Error('Kein ZIP-Endverzeichnis gefunden')
  const anzahl = buf.readUInt16LE(eocd + 10)
  let p = buf.readUInt32LE(eocd + 16)
  const out = new Map()
  for (let i = 0; i < anzahl; i++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) throw new Error(`Zentraleintrag ${i} kaputt`)
    const methode = buf.readUInt16LE(p + 10)
    const crc = buf.readUInt32LE(p + 16)
    const gross = buf.readUInt32LE(p + 20)
    const nLen = buf.readUInt16LE(p + 28)
    const xLen = buf.readUInt16LE(p + 30)
    const kLen = buf.readUInt16LE(p + 32)
    const lok = buf.readUInt32LE(p + 42)
    const name = buf.subarray(p + 46, p + 46 + nLen).toString('utf8')
    const start = lok + 30 + buf.readUInt16LE(lok + 26) + buf.readUInt16LE(lok + 28)
    const roh = buf.subarray(start, start + gross)
    const daten = methode === 8 ? zlib.inflateRawSync(roh) : methode === 0 ? roh : null
    if (!daten) throw new Error(`${name}: Methode ${methode} unbekannt`)
    if (crc32(daten) !== crc) throw new Error(`${name}: CRC passt nicht`)
    out.set(name, Buffer.from(daten))
    p += 46 + nLen + xLen + kLen
  }
  return out
}

// Unterschiede zwischen ZIP-Inhalt und Quellordner. Leere Liste = deckungsgleich.
export function zipGegenQuelle(zipBuf, dir, praefix) {
  const imZip = zipLesen(zipBuf)
  const unterschiede = []
  const quelle = dateienListe(dir)
  for (const rel of quelle) {
    const z = imZip.get(`${praefix}/${rel}`)
    if (!z) unterschiede.push(`fehlt in der ZIP: ${rel}`)
    else if (!z.equals(fs.readFileSync(path.join(dir, rel)))) unterschiede.push(`anderer Inhalt: ${rel}`)
  }
  const soll = new Set(quelle.map((r) => `${praefix}/${r}`))
  for (const name of imZip.keys()) if (!soll.has(name)) unterschiede.push(`nur in der ZIP: ${name}`)
  return unterschiede
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const alle = projekte()
  const wahl = process.argv.slice(2)
  const unbekannt = wahl.filter((n) => !alle.includes(n))
  if (unbekannt.length) {
    console.error(`kein Projekt-Ordner: ${unbekannt.join(', ')}`)
    process.exit(1)
  }
  for (const name of wahl.length ? wahl : alle) {
    const ziel = zipPfad(name)
    fs.mkdirSync(path.dirname(ziel), { recursive: true })
    const buf = zipBauen(quellOrdner(name), name)
    fs.writeFileSync(ziel, buf)
    console.log(`geschrieben: ${path.relative(ROOT, ziel)} (${dateienListe(quellOrdner(name)).length} Dateien, ${buf.length} Bytes)`)
  }
}
