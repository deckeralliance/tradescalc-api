# TradesCalc API — Social Media Copy

## LinkedIn Posts

### Post 1: Launch Announcement

**I just shipped an API for the trades industry — and it's live on RapidAPI.**

For the past few months, I've been building TradesCalc: a REST API that handles the engineering calculations that trades professionals do every day.

Here's what it covers:

⚡ **Electrical** — NEC 2023 ampacity lookups, voltage drop, conduit fill, box fill, breaker sizing, wire sizing, and derating. All from Table 310.16 and the formulas in Chapter 9.

🔥 **Fire Protection** — Hydrant flow testing, Hazen-Williams friction loss, pump discharge pressure, needed fire flow, and ISO grading factors.

🏗️ **Utility** — IEEE 1366 reliability indices (SAIDI, SAIFI, CAIDI), major event day detection, and outage cost estimation.

25 endpoints. Three modules. Free tier on all of them.

I built this because I'm an engineer and operations manager at an electric cooperative. I was tired of rebuilding the same spreadsheets and manually flipping through NEC tables. So I put them behind an API.

If you're building tools for contractors, inspectors, or utility operators — or you're just tired of doing voltage drop by hand — check it out:

🔗 https://tradescalc.dev
📖 Docs: https://tradescalc.dev/docs

Free to try on RapidAPI:
→ https://rapidapi.com/deckeralliance/api/tradescalc

#API #ElectricalEngineering #NEC #Utility #FireProtection #Python #FastAPI #DevTools

---

### Post 2: Technical Deep-Dive

**One API call to replace flipping through NEC Table 310.16.**

If you've ever needed to look up conductor ampacity — copper, 12 AWG, 75°C insulation — here's what that looks like with TradesCalc:

```
POST /v1/electrical/ampacity
{
  "wire_size": "12",
  "material": "copper",
  "temp_rating": "75"
}
```

Response:
```json
{
  "ampacity": 25,
  "nec_reference": "NEC 2023 Table 310.16"
}
```

That's it. No PDF lookups. No cross-referencing columns. Every response includes the NEC reference so you can cite the source.

The API covers the full range of Table 310.16 — wire sizes 14 through 1000 kcmil, copper and aluminum, at 60°C, 75°C, and 90°C ratings. Plus voltage drop calculations, conduit fill analysis, box fill per Article 314, breaker sizing, and more.

It's designed for developers building contractor tools, estimating software, or field inspection apps. Or for engineers like me who got tired of spreadsheets.

Free tier available. No credit card required.

Try it → https://rapidapi.com/deckeralliance/api/tradescalc
Docs → https://tradescalc.dev/docs

#NEC2023 #ElectricalEngineering #API #RestAPI #DevTools #Python

---

### Post 3: Use-Case Story

**A utility engineer walks into a board meeting...**

Every quarter, I have to report our utility's reliability performance to the board. That means calculating SAIDI, SAIFI, and CAIDI from our outage data — sometimes 50+ events across three months.

The old process: Export from the outage management system. Paste into a spreadsheet. Fix the date formats. Run the formulas. Double-check the math. Build a slide.

The new process:

```python
response = requests.post(
    "https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability",
    json={
        "outage_events": outage_data,
        "total_customers_served": 15000,
        "period_description": "Q3 2024"
    },
    headers=headers
)
# SAIDI, SAIFI, CAIDI — computed in milliseconds
```

I built TradesCalc because I needed it. The reliability module takes raw outage event data — customers affected, duration in minutes — and returns IEEE 1366 indices instantly.

It also handles major event day detection using the 2.5-beta log-normal method, and estimates outage costs broken down by residential, commercial, and industrial customer classes.

If you're at a utility (co-op, muni, or IOU) and you're still doing reliability indices in Excel, this API might save you a few hours every quarter.

Free tier: https://rapidapi.com/deckeralliance/api/tradescalc-utility

*For estimation and planning purposes only.*

#UtilityEngineering #IEEE1366 #SAIDI #SAIFI #Reliability #API #PowerSystems

---

## X/Twitter Tweets

### Tweet 1: Launch Announcement

🚀 Just launched TradesCalc — a REST API for NEC electrical calcs, fire flow testing, and utility reliability indices.

25 endpoints. Free tier. Live now on RapidAPI.

https://tradescalc.dev

#API #NEC #ElectricalEngineering

---

### Tweet 2: Technical Deep-Dive

NEC ampacity lookup in one API call:

```
POST /v1/electrical/ampacity
{"wire_size":"12","material":"copper","temp_rating":"75"}
→ {"ampacity": 25, "nec_reference": "NEC 2023 Table 310.16"}
```

No more PDF table lookups. Free tier on RapidAPI ⚡

https://rapidapi.com/deckeralliance/api/tradescalc

---

### Tweet 3: Use-Case Story

Utility engineers: stop computing SAIDI/SAIFI/CAIDI in spreadsheets.

TradesCalc takes your raw outage events → returns IEEE 1366 indices in milliseconds.

Major event day detection included.

Free tier → https://rapidapi.com/deckeralliance/api/tradescalc-utility

#IEEE1366 #Utility #API
