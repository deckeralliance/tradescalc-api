## User Context — James

- **Profession**: Electrical Engineer, Operations Manager at an electric cooperative, active Firefighter
- **Domain expertise**: NEC electrical code, IEEE 1366 utility reliability indices, NFPA/NERIS fire incident reporting, outage management, service orders, ArcGIS/GIS
- **Technical level**: Engineering background, learning software development. Comfortable with concepts but new to Python/FastAPI/API development
- **Work style**: Prefers ambitious, comprehensive plans ("10X mindset") over minimum viable products. Wants to build real businesses, not side projects
- **Current tech stack**: Python + FastAPI for APIs, Render for hosting, RapidAPI for marketplace distribution
- **Files of interest**: Outage reports (xlsx), service order PDFs, budget spreadsheets, CRC 9012 equipment docs — all in Documents folder

## Active Project — TradesCalc API

- **What**: "TradesCalc" — The Infrastructure API for the Trades. A multi-API platform offering NEC electrical calculations, utility reliability indices (SAIDI/SAIFI/CAIDI), and fire protection engineering calculations
- **Workspace**: `C:\Users\jamesw\Documents\antigravity\hopeful-mendeleev`
- **Stack**: Python 3.12 + FastAPI + Pydantic + Uvicorn, deployed to Render, listed on RapidAPI
- **Architecture**: Modular — `src/tradescalc/` with routers/, services/, models/, data/ directories. NEC tables stored as JSON, loaded at startup via NECDataStore singleton
- **RapidAPI account**: Personal Account (deckeralliance). Demo project exists for reference
- **Revenue model**: Split listings per module on RapidAPI (Free → $99.99/mo per module) + future direct billing via Stripe
- **Plans**: See `tradescalc_10x_plan.md` artifact for full 12-month roadmap
- **Status**: v0.1.0 LIVE — 25 endpoints deployed to Render, 3 RapidAPI listings (Electrical, Fire, Utility) all PUBLIC
- **GitHub**: https://github.com/deckeralliance/tradescalc-api
- **Live API**: https://tradescalc-api.onrender.com
- **RapidAPI listings**:
  - https://rapidapi.com/deckeralliance/api/tradescalc (Electrical)
  - https://rapidapi.com/deckeralliance/api/tradescalc-fire (Fire)
  - https://rapidapi.com/deckeralliance/api/tradescalc-utility (Utility)

## Revenue Goal — API Passive Income

- **Strategy**: Build and list niche APIs on RapidAPI using domain expertise
- **Workflow**: Use the `api-factory` skill for repeatable end-to-end builds
- **Stack**: Python + FastAPI → Render → RapidAPI (split listings per module)
- **Current products**: TradesCalc (Electrical, Fire, Utility)
- **Target**: Multiple API products across trades/engineering niches
- **Key accounts**: GitHub (deckeralliance), Render (GitHub SSO), RapidAPI (deckeralliance)
- **Pricing principle**: Price by buyer persona budget, not by cost. Split modules when personas differ.
