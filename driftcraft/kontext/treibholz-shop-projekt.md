# Treibholz-Türgriffe Shop

Schlanker E-Commerce für handgefertigte Unikate aus Treibholz. Keine Plugin-Hölle, kein Shop-System, kein Vendor-Lock-in.

## Produkt

Türgriffe aus Treibholz. Jedes Stück ein Einzelstück. Kein klassisches Inventory, sondern eine kuratierte Galerie verfügbarer Werke.

## Rechtlicher Rahmen

- **Rechtsform:** Individual Entrepreneur (IE), Georgien
- **NACE-Codes:**
  - 90.03 — Artistic creation (künstlerische Schöpfung)
  - 32.99 — Other manufacturing n.e.c. (Kunsthandwerk, Deko-Objekte)
  - 47.91 — Retail sale via mail order / Internet
- **Steuerstatus:** Small Business Status anstreben (1% auf Umsatz, beim Revenue Service beantragen) — noch nicht beantragt, **Priorität vor erstem Verkauf**
- **Rechnungsstellung:** Revenue Service Georgia (RS Invoice Portal) — manuell zu Beginn, später API
- **Hinweis:** Virtuelle Zone nicht anwendbar (physische Waren)

## Stack

- **Frontend:** Astro auf Vercel (Hobby-Tier kostenlos)
- **Theme:** [Williamsburg](https://lexingtonthemes.com/templates/williamsburg) von Lexington Themes (Astro + Tailwind CSS, bereits mit Sanity verdrahtet) — Cart-Logik deaktiviert, Checkout direkt auf Stripe Payment Links
- **CMS & Bilder:** Sanity (Free Tier — 3 Nutzer, 10GB Assets, eingebautes Asset Management) — Schema: Foto, Maße, Holzart, Preis, Status, Stripe-Link
- **Payment:** Stripe Payment Links pro Stück
- **Rechnungsstellung:** RS Invoice (Revenue Service Georgia) — manuell via Portal
- **Webhook-Logik:** Vercel Serverless Functions → Sanity Mutations API

## Datenfluss

1. Neues Stück → Sanity Studio: Foto hochladen, Felder befüllen, Status `verfügbar`
2. Stripe Payment Link manuell erstellen, URL in Sanity eintragen
3. Astro-Site rendert alle Stücke mit Status `verfügbar` als Galerie
4. Kunde klickt → Stripe Checkout → Zahlung
5. Stripe-Webhook → Serverless Function:
   - Sanity Mutations API: Status auf `verkauft` setzen
   - Mail an dich: „Stück X verpacken und versenden"
6. Rechnung manuell über RS Invoice Portal ausstellen

## Architektur-Prinzipien

- Jede Komponente austauschbar (keine proprietären Verschachtelungen)
- Alles redet über simple REST-APIs
- Verkaufte Stücke werden archiviert, nicht gelöscht (Buchhaltung)
- Eine Schicht nach der anderen aufbauen, nicht parallel

## Reihenfolge der Umsetzung

1. **Small Business Status beim Revenue Service beantragen** ← vor allem anderen
2. Williamsburg Theme kaufen, Sanity-Projekt anlegen
3. Sanity-Schema für Stücke definieren (Foto, Maße, Holzart, Preis, Status, Stripe-Link)
4. 5 Dummy-Stücke in Sanity anlegen, Galerie lokal testen
5. Astro + Williamsburg auf Vercel deployen
6. RSS-Feed aktivieren (Astro built-in) → SEO und Newsletter
7. Blog: erste 3–5 Artikel (aus YouTube-Scripts)
8. Stripe Payment Links pro Stück anbinden (manuell)
9. Webhook für Status-Update via Sanity Mutations API
10. RS Invoice API-Integration (wenn Volumen es rechtfertigt)
11. Versand-Workflow (manuell, bei Unikaten okay)

## Kosten (geschätzt)

- Vercel Hobby: 0 €
- Williamsburg Theme (Lexington): ~99$ Einzellizenz oder 99$ All Access (derzeit halbiert)
- Sanity Free: 0 € (3 Nutzer, 10GB)
- Stripe: nur Transaktionsgebühren (~1,5 % + 0,25 €)
- RS Invoice: kostenlos (staatliches Portal)
- Steuer (Small Business): 1% auf Umsatz

## Was bewusst weggelassen wird

- Warenkorb (bei Unikaten konzeptionell unsinnig)
- Varianten-Logik (jedes Stück ist seine eigene Variante)
- Bestandszählung (Status `verfügbar` / `verkauft` reicht)
- User-Accounts (Gast-Checkout via Stripe)
- Bewertungen, Wishlist, Cross-Selling (nicht zur Markenstory passend)
- Automatisierte Rechnungs-API initial (manuell reicht für Unikat-Volumen)

## Skalierungspfade

- Sanity zu klein → selbst gehostetes CMS (Payload, Directus)
- Mehr Stücke, mehr Traffic → Astro im SSR-Modus statt statisch
- Serien statt Unikate → Inventory-Felder in Sanity, weiterhin kein Shop-System nötig
- Internationale Verkäufe → OSS-Schwelle 10.000 € beachten (gilt auch für IE in Georgien bei EU-Kunden)
- Rechnungs-Automatisierung → RS Invoice API wenn Volumen > ~20 Verkäufe/Monat

## Versand (Nomaden-Modus)

- Versand erfolgt aus wechselnden EU-Ländern (Camper-Betrieb)
- Kein fixer Carrier-Vertrag — **Pirateship oder Shippo** als Label-Aggregator (online kaufen, lokal drucken)
- Verpackungsmaterial kompakt und reisefähig halten
- Fulfillment-Agentur (3PL) geplant, Standort offen — Kandidaten wenn Volumen steigt: **Byrd, Sendcloud-Netzwerk** (kein Mindestvolumen)
- **Steuerlich klären:** Versand aus wechselnden EU-Ländern als georgischer IE — MwSt-Behandlung B2C EU, OSS-Schwelle 10.000 €, mit Steuerberater abstimmen

## Offene Punkte

- **Small Business Status beantragen** (Revenue Service Georgia) — vor erstem Verkauf
- Buchhaltungssoftware für georgische IE klären (Wave, Zoho Books, oder manuell?)
- MwSt-Status EU klären (Steuerberater, kein DIY)
- Zoll / Export-Dokumentation: CN22/CN23, Warenwert korrekt deklarieren (>150€ = zollpflichtig für Käufer)
- Foto-Setup: AI-gestützt via Clipdrop (Hintergrund entfernen + Studio-Setting) — Camper-tauglich
- Domain und Branding
