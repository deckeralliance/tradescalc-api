# SAIDI SAIFI CAIDI Calculator API — Automate IEEE 1366 Reliability Indices

## What Are SAIDI, SAIFI, and CAIDI?

Every utility — whether a cooperative, municipal, or investor-owned — must track and report reliability performance. The three core indices defined by IEEE Standard 1366 are:

- **SAIDI** (System Average Interruption Duration Index) — Average outage minutes per customer served
- **SAIFI** (System Average Interruption Frequency Index) — Average number of interruptions per customer served
- **CAIDI** (Customer Average Interruption Duration Index) — Average outage duration per affected customer

These indices drive regulatory filings, board reports, rate cases, and capital improvement planning. The TradesCalc **SAIDI SAIFI CAIDI calculator API** computes all three from your raw outage event data in a single request.

## How the SAIDI SAIFI CAIDI Calculator API Works

Feed in your outage events (customers affected and duration) plus total customers served. The API returns all three IEEE 1366 indices along with aggregate statistics.

**Endpoint:** `POST /v1/utility/reliability`

```bash
curl -X POST "https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc-utility.p.rapidapi.com" \
  -d '{
    "outage_events": [
      {"customers_affected": 450, "duration_minutes": 120},
      {"customers_affected": 200, "duration_minutes": 45},
      {"customers_affected": 1200, "duration_minutes": 90}
    ],
    "total_customers_served": 15000,
    "period_description": "Q3 2024"
  }'
```

**Response:**

```json
{
  "saidi": 11.2,
  "saifi": 0.1233,
  "caidi": 90.8108,
  "total_customer_minutes": 168000.0,
  "total_customer_interruptions": 1850,
  "period": "Q3 2024"
}
```

## Why Automate Reliability Index Calculations?

Most utility engineers compute SAIDI, SAIFI, and CAIDI in spreadsheets — pulling data from outage management systems, formatting it manually, and applying formulas. This works, but it's:

- **Time-consuming** for quarterly and annual reporting cycles
- **Error-prone** when handling dozens or hundreds of outage events
- **Hard to integrate** into dashboards, board report generators, or regulatory filing systems

A **SAIDI SAIFI CAIDI calculator API** lets you automate the entire workflow. Export outage events from your OMS, POST them to the API, and get standards-compliant indices back instantly.

## Additional Utility Endpoints

Beyond the SAIDI SAIFI CAIDI calculator, TradesCalc provides:

- **Major Event Day Detection** — IEEE 1366 2.5-beta log-normal method (TMED threshold)
- **Outage Cost Estimation** — Economic impact broken down by residential, commercial, and industrial customer classes

📖 **Full documentation:** [tradescalc.dev/docs](https://tradescalc.dev/docs)

## Try the SAIDI SAIFI CAIDI Calculator API Free

The Utility module is live on RapidAPI with a free tier. Test it in the interactive playground with your own outage data.

→ **[Try it free on RapidAPI](https://rapidapi.com/deckeralliance/api/tradescalc-utility)**

---

*For estimation and planning purposes only. All calculations should be verified before use in regulatory filings or official reports.*
