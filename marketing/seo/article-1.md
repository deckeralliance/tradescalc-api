# NEC Ampacity Table Lookup API — Automate Table 310.16

## Why You Need an NEC Ampacity Table Lookup API

Every electrical design starts with the same question: what's the allowable ampacity for this conductor? The answer lives in NEC Table 310.16 — a grid of values organized by wire size, conductor material, and insulation temperature rating.

If you're building software for electrical contractors, estimating platforms, or field inspection tools, you need that data programmatically. The TradesCalc **NEC ampacity table lookup API** gives you instant access to Table 310.16 values via a simple REST endpoint.

## How the NEC Ampacity Table Lookup API Works

Send a POST request with the wire size, material, and temperature rating. Get back the ampacity value with the NEC reference.

**Endpoint:** `POST /v1/electrical/ampacity`

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

## What the API Covers

The NEC ampacity table lookup API returns values for the complete range of NEC Table 310.16:

- **Wire sizes:** 14 AWG through 1000 kcmil
- **Materials:** Copper and aluminum
- **Temperature ratings:** 60°C, 75°C, and 90°C insulation
- **Standard:** NEC 2023

Every response includes the `nec_reference` field so your application can cite the source.

## Use Cases for the NEC Ampacity Lookup API

- **Estimating software** — Automatically size conductors during bid preparation
- **Field inspection apps** — Verify installed conductor ratings on the job site
- **Electrical design tools** — Integrate NEC-compliant ampacity data into CAD or BIM workflows
- **Training platforms** — Build interactive NEC lookup tools for apprentice electricians

## Additional Electrical Endpoints

Beyond ampacity lookups, TradesCalc provides endpoints for voltage drop, conduit fill, box fill, breaker sizing, wire sizing, service entrance calculations, ampacity derating, and transformer sizing — all referencing NEC 2023.

📖 **Full documentation:** [tradescalc.dev/docs](https://tradescalc.dev/docs)

## Try the NEC Ampacity Table Lookup API Free

TradesCalc is live on RapidAPI with a free tier — no credit card required. Test it in the interactive playground and see the results instantly.

→ **[Try it free on RapidAPI](https://rapidapi.com/deckeralliance/api/tradescalc)**

---

*For estimation and planning purposes only. All calculations should be verified by a licensed professional. Not a substitute for the NEC codebook.*
