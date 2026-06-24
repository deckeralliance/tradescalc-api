---
title: I Built an API That Does NEC Electrical Calculations So You Don't Have To
published: false
description: TradesCalc is a REST API for NEC ampacity lookups, voltage drop, conduit fill, fire flow testing, and utility reliability indices. Free tier on RapidAPI.
tags: api, electrical, python, webdev
cover_image:
---

## The Problem: Spreadsheets, PDFs, and Table Lookups

If you've ever had to look up an ampacity value from NEC Table 310.16, calculate voltage drop for a 200-foot feeder run, or compute SAIDI/SAIFI indices from a year of outage data, you know the drill:

1. Crack open the NEC codebook (or a PDF)
2. Find the right table for your conductor material and temperature rating
3. Plug numbers into a spreadsheet formula you copy-pasted from somewhere
4. Hope you didn't fat-finger a decimal point

I'm an electrical engineer and operations manager at an electric cooperative. I do these calculations constantly — for service upgrades, outage reports, fire flow tests, and board presentations. After building the same spreadsheet for the third time, I decided to build an API instead.

## The Solution: TradesCalc API

**TradesCalc** is a REST API that handles NEC-compliant electrical calculations, fire protection engineering, and utility reliability indices. It's live on [RapidAPI](https://rapidapi.com/deckeralliance/api/tradescalc) with a **free tier** — no credit card required.

Here's what it covers across 25 endpoints:

| Module | Endpoints | Standards |
|--------|-----------|-----------|
| ⚡ Electrical | Ampacity, voltage drop, wire sizing, conduit fill, box fill, breaker sizing, derating, service entrance, transformer sizing | NEC 2023 |
| 🔥 Fire | Hydrant flow, friction loss, pump pressure, needed fire flow, ISO grading | NFPA / ISO |
| 🏗️ Utility | SAIDI/SAIFI/CAIDI, major event day detection, outage cost estimation | IEEE 1366 |

## Show Me the Code

### 1. Look Up Ampacity (NEC Table 310.16)

What's the ampacity of 12 AWG copper at 75°C? One API call:

**cURL:**

```bash
curl -X POST "https://tradescalc.p.rapidapi.com/v1/electrical/ampacity" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc.p.rapidapi.com" \
  -d '{"wire_size": "12", "material": "copper", "temp_rating": "75"}'
```

**Response:**

```json
{
  "wire_size": "12",
  "material": "copper",
  "temp_rating": "75",
  "ampacity": 25,
  "nec_reference": "NEC 2023 Table 310.16"
}
```

### 2. Calculate Voltage Drop

Running a 30A load on 10 AWG copper, 150 feet, single-phase at 240V:

**Python:**

```python
import requests

url = "https://tradescalc.p.rapidapi.com/v1/electrical/voltage-drop"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc.p.rapidapi.com"
}
payload = {
    "load_amps": 30,
    "voltage": 240,
    "distance_ft": 150,
    "wire_size": "10",
    "material": "copper",
    "phase": "single",
    "conduit_type": "pvc",
    "power_factor": 1.0
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### 3. Fire Hydrant Flow Testing

Just ran a flow test? Static: 65 psi, residual: 40 psi, flow: 880 GPM. What's available at 20 psi residual?

**JavaScript:**

```javascript
const response = await fetch(
  "https://tradescalc-fire.p.rapidapi.com/v1/fire/hydrant-flow",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc-fire.p.rapidapi.com",
    },
    body: JSON.stringify({
      static_pressure_psi: 65,
      residual_pressure_psi: 40,
      flow_at_residual_gpm: 880,
    }),
  }
);

const data = await response.json();
console.log(`Available flow at 20 psi: ${data.available_flow_at_20psi_gpm} GPM`);
```

### 4. Utility Reliability Indices (SAIDI/SAIFI/CAIDI)

Feed in your outage events, get IEEE 1366 indices back:

```python
import requests

url = "https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc-utility.p.rapidapi.com"
}
payload = {
    "outage_events": [
        {"customers_affected": 450, "duration_minutes": 120},
        {"customers_affected": 200, "duration_minutes": 45},
        {"customers_affected": 1200, "duration_minutes": 90}
    ],
    "total_customers_served": 15000,
    "period_description": "Q3 2024"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
print(f"SAIDI: {data['saidi']} | SAIFI: {data['saifi']} | CAIDI: {data['caidi']}")
```

## Why Not Just Use a Spreadsheet?

Spreadsheets are fine for one-off calculations. But if you're:

- **Building an app** for contractors or inspectors in the field
- **Automating reports** that pull from outage management systems
- **Integrating NEC lookups** into an estimating or design tool
- **Generating board reports** with up-to-date reliability metrics

...then you need an API, not a spreadsheet.

TradesCalc gives you the same NEC tables and engineering formulas behind a clean REST interface. JSON in, JSON out. Every response includes the NEC reference so you can cite it.

## Try It Free

All three modules are live on RapidAPI with a free tier:

- ⚡ [TradesCalc — Electrical](https://rapidapi.com/deckeralliance/api/tradescalc)
- 🔥 [TradesCalc — Fire](https://rapidapi.com/deckeralliance/api/tradescalc-fire)
- 🏗️ [TradesCalc — Utility](https://rapidapi.com/deckeralliance/api/tradescalc-utility)

Each listing has a live playground where you can test endpoints before writing a line of code.

📖 **Full docs:** [tradescalc.dev/docs](https://tradescalc.dev/docs)
🔗 **GitHub:** [github.com/deckeralliance/tradescalc-api](https://github.com/deckeralliance/tradescalc-api)

---

> ⚠️ **Disclaimer:** TradesCalc is for estimation and planning purposes only. All calculations should be verified by a licensed professional before use in design or construction. Not a substitute for the NEC codebook.

---

*Built with Python, FastAPI, and too many late nights cross-referencing NEC tables. Questions or feature requests? Open an issue on [GitHub](https://github.com/deckeralliance/tradescalc-api).*
