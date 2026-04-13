# CotMatch — UK Neonatal Unit Directory

> **A progressive web app for rapid neonatal unit lookup, clinical criteria matching, and transport coordination across the United Kingdom.**

[![PWA](https://img.shields.io/badge/PWA-Offline%20Ready-4A90E2?style=flat-square&logo=pwa)](https://apkumar.github.io/cotmatch/)
[![Units](https://img.shields.io/badge/Units-197%20UK%20Neonatal%20Sites-2ecc71?style=flat-square)](#database-methodology)
[![License: GNU Affero](https://img.shields.io/badge/license-AGPLv3-red.svg?style=flat-square)](LICENSE)

---

## What is CotMatch?

CotMatch is a **fast, clinically intelligent directory** of UK neonatal units — accessible from any smartphone, tablet or desktop, with no app store required.

It is designed for the moments that matter most: when a baby needs to be transferred urgently and the clinical team needs to quickly identify which units can safely accept them based on **gestational age, birth weight, level of care, and specialist capabilities** — without fumbling through a ring binder or waiting in a switchboard queue.

The tool allows users to:

- **Filter by clinical criteria** — level of care (NICU/LNU/SCBU), minimum weight, minimum gestation, and specific capabilities such as iNO, ECMO, active cooling, on-site surgery, PICU co-location, and more
- **Search instantly** by hospital name, trust, postcode, ODN, or transport team — including abbreviated names, alternative spellings, and partial strings
- **Sort by proximity** — enter your postcode to rank units by distance from your location, or browse from central London by default
- **Access contact details in one tap** — direct dial numbers for neonatal units and regional transport teams

---

## Why CotMatch?

Finding a cot during a neonatal emergency should never depend on whether someone knows the direct dial number off the top of their head, or how recently the PDF in the shared drive was updated.

**CotMatch puts the information directly into the hands of the clinical team:**

- A neonatal flow coordinator can identify matching units and begin outreach in under 30 seconds
- A repatriation coordinator can filter by home region and capability to plan a step-down transfer
- A nurse in charge at 3am can dial a transport team without navigating an IVR switchboard
- An ODN governance team can review network-level capability data at a glance

The unit database is searchable, proximity-sorted, and structured around the **BAPM Framework for Practice (2019)** three-tier designation system — the same classification system used across NHS England, Scotland, Wales, and Northern Ireland.

---

## Everything We've Built So Far

### 🗂️ National Neonatal Unit Database
- **197 UK neonatal units** across England, Scotland, Wales, and Northern Ireland — the most complete open-access neonatal directory available
- Every unit fully geocoded with precise latitude/longitude coordinates via the `postcodes.io` API, enabling accurate distance calculations
- Data reconciled from BAPM registers, NHS ODN directories, individual trust websites, the Wales Neonatal Network, Scottish Perinatal Network (Best Start), and HSCNI
- Each unit stores both an **abbreviated display name** and a **full expanded name** — so searching `Q. Elizabeth Hosp` and `Queen Elizabeth Hospital Woolwich` both return the correct card
- Capability data follows the **BAPM 2019 three-tier framework** with unit-specific overrides where verified data is available
- Structured JSON schema covering nursing capabilities, advanced facilities, specialties, ODN assignment, transport team, phone numbers, address, postcode, and geolocation

### 🔍 Intelligent Search
- **Grep-style fuzzy search bar** — begins showing results from 2 characters, matching across hospital name, full name, NHS trust, postcode, ODN, and transport team simultaneously
- Supports **partial strings**, **abbreviations**, and **misspelled queries** using a dual-strategy matching engine: word-by-word substring match first, subsequence fallback for typos
- **Dropdown suggestions** appear instantly as you type — click any result to isolate that unit card
- **Clear (✕) button** appears as soon as you start typing, resetting the full directory view in one tap
- Postcode search — typing a postcode (e.g. `SE1`) will surface matching units

### 📍 Proximity Sorting
- Enter any UK postcode in the location field to sort all results **nearest first** using Haversine-formula distance calculations
- Falls back gracefully to **SW1A 0AA (Westminster)** as the default sort origin when no postcode is provided — ensuring a clinically sensible geographic default for a nationally-used tool
- Distance in miles displayed on every unit card

### 🏥 Clinical Capability Filtering
- **Level of care filter** — SCBU (L1), LNU (L2), NICU (L3) — filters upward (selecting L2 shows L2 and L3 units)
- **Weight filter** — enter birth weight in grams; units unable to accept below that threshold are excluded
- **Gestation filter** — enter corrected gestational age in weeks
- **ODN / Network filter** — dropdown to isolate one of 12 named UK neonatal networks
- **Advanced facilities checkboxes:** iNO, ECMO, Active Cooling, Laser for ROP, On-site PICU
- **Specialty checkboxes:** On-site General Surgery, Neurosurgery, On-site Cardiology, Paediatric ENT, Paediatric Anaesthetic Support, Long-Term Ventilation
- **Nursing capability checkboxes:** CPAP/HHFNC, Hourly NGT feeds, NJT care, Continuous pump feeds, Parenteral Nutrition, Long-line/PICC, Broviac/Hickman, Ventricular taps, Convulsion management, Stoma care, Tracheostomy care, Palliative care

### 📋 Unit Cards
- Clean card layout displaying: unit name, NHS trust (as clickable link to trust website), address, full postcode, distance, capability badges (colour-coded), accepts from weight, accepts from gestation, level badge
- **ODN name as a clickable hyperlink** to the ODN's official website (e.g. London ODN → londonneonatalnetwork.org.uk)
- **One-tap dial** for the direct neonatal unit number
- **Transport team** name and direct number displayed on every card
- Clinical data (weight/gestation limits) displayed with clear line breaks — no truncation
- Capability badges visually grouped: red for advanced/specialist, lighter for routine capabilities

### 📱 Progressive Web App (PWA)
- **Installable** to iPhone/Android home screen without an app store — works like a native app
- **Offline capable** via Service Worker with Network-First caching strategy — the full directory remains accessible without a connection after first load
- Cache versioning system ensures users always receive the latest data on reconnection without stale content persisting
- `manifest.json` configured for standalone display, correct theme colour, and icons

### 🌐 ODN Network Coverage
All 12 UK neonatal networks mapped:

| Network | Coverage |
|---|---|
| London | Greater London |
| North West | Lancashire, Cheshire, Merseyside, Cumbria |
| Northern | North East England |
| Yorkshire & Humber | Yorkshire, Humber |
| East Midlands | Nottinghamshire, Derbyshire, Lincolnshire, Northamptonshire |
| West Midlands | West Midlands, Worcestershire, Staffordshire |
| SSBC | Staffordshire, Shropshire, Black Country |
| East of England | East Anglia, Hertfordshire, Bedfordshire |
| Thames Valley & Wessex | Thames Valley, Hampshire, Dorset |
| Kent, Surrey & Sussex | South East England |
| South West | Devon, Cornwall, Somerset, Bristol |
| Scotland | All Scottish Health Boards (ScotSTAR transport) |
| Wales | All Welsh Health Boards (CHANTS transport) |
| Northern Ireland | All HSCNI Trusts (NISTAR transport) |

### 🔄 Data Integrity Tracking
- **Closures and downgrades tracked in real-time** — units that have permanently closed (Royal Free, Horton General, Yeovil District) removed from the dataset; units that have been downgraded (Countess of Chester → L1 SCBU, University Hospital Wishaw → L2 LNU) correctly flagged
- **Relocations updated** — e.g. Poole Hospital → Royal Bournemouth Hospital BEACH Building (closed 31 March 2025)
- **Duplicate detection** — ghost entries introduced by name-matching conflicts during data ingestion identified and corrected (e.g. Fife Victoria Hospital incorrectly duplicated across Blackpool and Newcastle entries)
- Abbreviated trust names normalised — all trusts end with the correct legal suffix (NHS Trust, NHS Foundation Trust, etc.)

---

## How to Use

### Searching

The search bar at the top of the directory supports **natural language queries**:

| What you type | What it finds |
|---|---|
| `queen elizabeth woolwich` | Q. Elizabeth Hosp (South London) |
| `gosh` | Great Ormond Street Hospital |
| `edinburgh nicu` | Edinburgh Royal Infirmary |
| `KSS` | All units in the Kent, Surrey & Sussex network |
| `SE1` | Units near that postcode area |
| `ecmo` | Search by capability in filter panel |

> **Tip:** The search is fuzzy — it searches across hospital name, full name, trust, postcode, ODN, and transport team simultaneously. You do not need exact spelling.

### Filtering by Clinical Criteria

Use the **filter panel** on the left to narrow results by:

- **Patient weight** — enter the baby's current weight in grams; units that cannot accept below this threshold are excluded
- **Gestational age** — enter corrected gestational age in weeks
- **Minimum level of care** — SCBU (L1), LNU (L2), or NICU (L3)
- **ODN / Network** — filter to a specific Operational Delivery Network
- **Capabilities** — tick boxes for iNO, ECMO, active cooling, laser for ROP, PICU access, on-site neurosurgery, on-site cardiac, general surgery, paediatric ENT, LTV, palliative care, and a range of nursing capabilities

### Location-Based Sorting

- Enter your **postcode** in the location field and click **Locate** to sort all results by driving distance from that point
- Without a postcode, results sort by proximity from **SW1A 0AA** (Westminster) by default
- Distance is shown in miles on each unit card

### Contacting a Unit

Each card displays:
- **Direct neonatal unit number** — tap to dial on mobile
- **Network / ODN** — tappable link to the ODN's official website
- **Transport team** and contact number

---

## Tips for Clinical Users

1. **Bookmark to your home screen.** CotMatch is a Progressive Web App — on iPhone, tap the Share icon and select *Add to Home Screen*. On Android, tap the browser menu and select *Install App*. It then works offline.

2. **Use the proximity filter during busy escalation calls.** If multiple NICU beds are available, sorting by distance helps prioritise the geographically nearest appropriate unit first, minimising neonatal transport time.

3. **Check capability badges quickly.** Each unit card shows coloured capability tags (e.g. ECMO, Cooling, iNO, Neurosurg). Red indicates a specialist intervention capability — scan these first when the clinical query is complex.

4. **The search bar clears with the ✕ button** — you can reset back to the full directory without refreshing the page.

5. **Always verify critical contact numbers** before acting on them. See [Disclaimer](#disclaimer) below.

---

## Database Methodology

The CotMatch database (`uk_neonatal_units.json`) currently covers **~197 neonatal units** across England, Scotland, Wales, and Northern Ireland.

### Data Sources

Unit data was compiled and cross-referenced from multiple authoritative sources:

| Source | Used For |
|---|---|
| **BAPM Unit Register** | Level designation, capability classification |
| **NHS England Neonatal ODN Directories** | Network assignment, transport team mapping |
| **Individual NHS Trust websites** | Direct unit telephone numbers, address verification |
| **Scottish Perinatal Network (Best Start)** | Scottish unit data and current NICU designations |
| **Wales Neonatal Network** | Welsh unit contacts |
| **HSCNI** | Northern Ireland neonatal contacts |
| **postcodes.io API** | Precise latitude/longitude geocoding for proximity sorting |

### Capability Classification

Clinical capabilities are assigned using **BAPM's three-tier framework** as a baseline, with individual unit-level overrides applied where verified information is available:

- **Level 3 (NICU):** Full intensive care including ventilation, surgery access, and advanced therapies such as iNO and ECMO where applicable
- **Level 2 (LNU):** High dependency care including CPAP, parenteral nutrition, and level 1 surgical support
- **Level 1 (SCBU):** Special care for stable and convalescent infants

### Known Limitations

- Capability data for some units (particularly those from sparse geographic sources) is **inferred from BAPM designation level** rather than individually verified
- Contact numbers are sourced from NHS trust websites and ODN directories at the time of data collection and **may not reflect the most recent updates**
- Unit closures, downgrades, and relocations are tracked manually — see [Reporting Inaccuracies](#reporting-inaccuracies)

---

## Getting Started

### Use the hosted version

Simply go to:

**[https://apkumar.github.io/cotmatch/](https://apkumar.github.io/cotmatch/)**

No account, no login, no installation required.

---

### Run your own local version

If you are an ODN or trust wishing to host a private instance with customised data:

**Requirements:** Any static file server (Python, Node, nginx, Apache, GitHub Pages, Netlify, etc.)

```bash
# Clone the repository
git clone https://github.com/apkumar/cotmatch.git
cd cotmatch

# Option 1: Python (built into macOS/Linux)
python3 -m http.server 8080
# Then open: http://localhost:8080

# Option 2: Node.js
npx serve .
# Then open the URL shown in the terminal
```

> **Note:** The app must be served via HTTP/HTTPS — not opened directly as a file (`file://`) — for the service worker and geolocation features to function.

### Customising the database

All unit data lives in `uk_neonatal_units.json`. Each entry follows this structure:

```json
{
  "unit_name": "Short display name",
  "unit_name_full": "Full expanded name for search indexing",
  "unit_postcode": "EC1A 1BB",
  "address": "Full street address",
  "trust": "NHS Trust Name",
  "trust_full": "Full trust name for search",
  "network_odn": "Short ODN label",
  "regional_transport_team": "Transport team name",
  "telephone_numbers": ["020 7234 5678"],
  "transport_telephone": "0800 123 456",
  "latitude": 51.5200,
  "longitude": -0.0980,
  "accepts_weight_from": 500,
  "accepts_gestation_from": 23,
  "minimum_level_of_care": 3,
  "nursing_capabilities": { "cpap_hhfnc": true, "parenteral_nutrition": true, "..." : "..." },
  "advanced_facilities": { "ino": true, "active_cooling": true, "respiratory_ecmo": false, "..." : "..." },
  "specialties": { "on_site_gen_surgery": true, "on_site_neurosurgery": false, "..." : "..." }
}
```

---

## Reporting Inaccuracies

Neonatal services change. Units downgrade, relocate, close, or update their contact details regularly. Keeping this database accurate is a collective effort.

**If you notice incorrect information** — a wrong phone number, a closed unit still listed, a capability incorrectly flagged — please raise it via one of the following:

- **GitHub Issue:** [Open an issue](https://github.com/apkumar/cotmatch/issues/new) with the unit name, the incorrect field, and the correct value with a source link if possible
- **Pull Request:** If you are comfortable with JSON, edit `uk_neonatal_units.json` directly and submit a PR
- **Email:** Contact details in the project maintainer section below

We aim to review and apply corrections within 48 hours.

---

## Getting Help

- **GitHub Issues:** For bug reports, data corrections, and feature requests — [github.com/apkumar/cotmatch/issues](https://github.com/apkumar/cotmatch/issues)
- **Discussions:** For broader questions about the methodology or clinical use cases — [github.com/apkumar/cotmatch/discussions](https://github.com/apkumar/cotmatch/discussions)

---

## Maintainers and Contributors

CotMatch is maintained by **[apkumar](https://github.com/apkumar)**, a clinician with a background in neonatal medicine.

Contributions are welcome from:
- Neonatologists and neonatal nurses who can validate capability data
- ODN governance and network coordinators with access to authoritative unit registers
- Clinical informatics professionals with experience in NHS data standards
- Developers wishing to improve the search, UI, or offline capabilities

Please open a pull request or issue to get involved.

---

## Disclaimer

> ⚠️ **IMPORTANT — Please read before clinical use**

CotMatch is provided as a **directory aid only**. It is **not** a validated clinical decision support tool and does not constitute medical advice.

- **Telephone numbers, addresses, and clinical capability data may be out of date.** Always verify critical contact details via the unit's official NHS trust website or your regional ODN before acting on them in a clinical emergency.
- **Unit capabilities listed are indicative**, based on BAPM designation and available published data. They do not replace direct clinical consultation with the receiving unit.
- **Bed availability is not shown.** CotMatch does not have access to real-time capacity data. Always confirm availability with the receiving unit before arranging transfer.
- The database reflects the best available information at the time of last update but **cannot guarantee accuracy** in a rapidly evolving NHS landscape where units close, downgrade, and relocate.

**In any time-critical clinical situation, contact your regional ODN transport line directly.** CotMatch is a tool to help you find who to call — not a substitute for that call.

---

*CotMatch — Because every second in neonatal care counts.*
