---
name: api-factory
description: >
  End-to-end workflow for building, testing, deploying, and listing a monetized
  API on RapidAPI. Takes a domain/niche and produces a live, revenue-generating
  API listing in under 2 hours. Uses FastAPI + Render + RapidAPI stack.
---

# API Factory — Build & Ship Monetized APIs

## Overview
Repeatable workflow for creating production-ready APIs from domain expertise
and listing them on RapidAPI for passive income. Proven on TradesCalc
(25 endpoints, 3 listings, built and deployed in 90 minutes).

## Prerequisites
- Python 3.11+ installed
- GitHub account connected (deckeralliance)
- Render account connected to GitHub
- RapidAPI account (deckeralliance)
- Git credentials cached

## Phase 1: Niche & Architecture (5 min)

### Identify the Niche
- Mine the user's professional expertise for underserved API markets
- Look for: calculations people do manually, reference data trapped in PDFs,
  industry-specific formulas not available as APIs
- Validate: search RapidAPI for existing competition (fewer = better)

### Define API Modules
- Group endpoints by buyer persona (who pays for this?)
- Each module becomes a separate RapidAPI listing
- Plan 5-15 endpoints per module
- Name each module for its target buyer, not internal architecture

### Architecture Decision
- Stack: Python 3.12 + FastAPI + Pydantic v2 + Uvicorn
- Deployment: Render (auto-deploy from GitHub via render.yaml)
- Marketplace: RapidAPI (separate listing per module)
- Data: JSON files loaded at startup via singleton DataStore pattern
- Auth: RapidAPI proxy secret middleware + optional direct API keys

## Phase 2: Scaffold (5 min)

### Project Structure Template
```
project-root/
├── pyproject.toml            # hatchling build, deps: fastapi, pydantic,
│                             #   pydantic-settings, uvicorn, python-dotenv
├── render.yaml               # Render auto-deploy config
├── README.md                 # Professional readme
├── .env.example              # Env var template
├── .gitignore                # Python gitignore
├── .github/workflows/ci.yml  # GitHub Actions CI (pytest on push/PR)
├── src/{project_name}/
│   ├── __init__.py           # Version string
│   ├── main.py               # FastAPI app with CORS + proxy auth middleware
│   ├── config.py             # pydantic-settings from env vars
│   ├── data/                 # JSON reference data files
│   ├── models/               # Pydantic v2 request/response models
│   │   └── {module}.py       # One file per API module
│   ├── routers/              # FastAPI endpoint routers
│   │   └── {module}.py       # One file per API module
│   └── services/             # Business logic + data access
│       └── data_store.py     # Singleton DataStore (load JSON at startup)
└── tests/
    ├── conftest.py           # Session-scoped data loading + TestClient fixture
    └── test_{module}.py      # One test file per module
```

### Key Patterns
- main.py: RapidAPI proxy secret validation middleware, CORS for all origins
- config.py: pydantic-settings with env var aliases, default dev values
- DataStore: Singleton loaded once at startup, accessed by all routers
- Each module: models/{module}.py + routers/{module}.py (never mix)
- Routers: POST for calculations, GET for reference data/lookups
- Placeholder endpoints: Return 501 with "Coming in v1.1" message

### pyproject.toml Dependencies
```toml
dependencies = [
    "fastapi[standard]>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27"]
```

## Phase 3: Build Data & Endpoints (20-30 min)

### Data Layer
- Encode reference data as JSON (tables, constants, lookup values)
- Create DataStore singleton service (load once at startup via lifespan)
- Include _meta fields for source attribution and disclaimers
- Validate against authoritative sources (codebooks, standards, specs)

### Parallel Build Strategy (CRITICAL FOR SPEED)
Launch subagents in parallel — one per API module:

```
Main Agent: Creates scaffold, data files, config, conftest.py
Subagent 1: Builds Module A models + router + tests
Subagent 2: Builds Module B models + router + tests
Subagent 3: Builds Module C models + router + tests
```

### Subagent Prompt Requirements
Give each subagent:
1. Exact file paths to create (models, router, tests)
2. Complete list of endpoints with method, path, formula/logic, response shape
3. All Pydantic model definitions with field names, types, constraints
4. Import paths for shared services (DataStore, config)
5. Error handling: 400 bad input, 404 not found, 422 validation, 501 placeholder
6. Test cases with engineering-verified expected values

### Model Conventions
- Pydantic v2 with Field() for descriptions, examples, constraints
- Literal types for constrained string choices
- Every request model has a matching response model
- Validation: ge=0, le=X, pattern=regex where appropriate
- Use descriptive field names matching industry terminology

### Router Conventions
- Every endpoint: operation_id, summary, description, response_model
- Use HTTPException for errors with clear detail messages
- POST for calculations, GET for reference data
- Include a GET /info endpoint per module (returns module description + endpoint list)
- Include a GET /health system endpoint (returns status + version)

## Phase 4: Test & Verify (5 min)

### Test Strategy
- Write tests alongside endpoints (subagents create both)
- Use engineering-verified expected values with source comments
- Test categories: valid input → correct output, edge cases, invalid input → 400/422
- conftest.py: session-scoped DataStore loading + TestClient fixture

### Run Locally Before Pushing
```bash
pip install -e ".[dev]"

# Lint and auto-fix
ruff check src/ tests/ --fix
ruff format src/ tests/

# Verify lint passes cleanly
ruff check src/ tests/
ruff format --check src/ tests/

# Run tests
pytest tests/ -v --tb=short
```

All 3 must pass (0 lint errors, 0 format changes, all tests green) before pushing.

### Common Fix Pattern
Tests usually fail on response shape mismatches (dict key names, list vs object).
Fix: align test assertions with actual response structure, not vice versa.

## Phase 5: Git + Deploy (5 min)

### Push to GitHub
```bash
git add -A
git commit -m "feat: {Project} API v0.1.0 — {N} endpoints, {M} tests passing"
git branch -M main
git remote add origin https://github.com/deckeralliance/{repo-name}.git
git push -u origin main
```
> **IMPORTANT**: The first `git push` must be done by the USER in their own
> PowerShell terminal. The agent's terminal cannot surface the Windows Git
> Credential Manager popup. After the first successful push, credentials are
> cached and all subsequent pushes work from the agent terminal.

### Deploy to Render
Use browser agent to:
1. Navigate to render.com (user logged in via GitHub SSO)
2. New + → Web Service → connect GitHub repo
3. Render auto-detects render.yaml
4. Add env vars: {PROJECT}_ENV=production, RAPIDAPI_PROXY_SECRET=(blank for now)
5. Deploy → wait for "Live" status (~2-3 min)
6. Verify: GET /health and browse /docs

> **NOTE**: Render Free tier spins down after 15 min of inactivity. First
> request after idle takes ~30 seconds (cold start). This affects RapidAPI
> latency metrics. Recommend upgrading to Starter ($7/mo) once the API gets
> its first paying subscriber. Until then, Free tier costs $0.

### render.yaml Template
```yaml
services:
  - type: web
    name: {project-name}
    runtime: python
    plan: free
    buildCommand: pip install -e ".[dev]"
    startCommand: uvicorn src.{project_name}.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.12"
```

## Phase 6: Brand & List (15 min)

### Generate Logos
One logo per API module using generate_image tool:
- Template: "Professional modern app icon, dark navy background (#0a0e1a),
  [SYMBOL] in [ACCENT_COLOR], circuit-board background pattern, no text,
  500x500, rounded corners, premium feel"
- Color palette by domain:
  - Electrical/engineering: amber/gold (#FFB800)
  - Fire/safety: red-orange (#FF4500)
  - Data/analytics: blue (#4A90D9)
  - Environmental: green (#2ECC71)
  - Healthcare: teal (#1ABC9C)

### RapidAPI Listing (per module)
Follow the `rapidapi-studio-listing` skill for detailed UI navigation.

**Critical order of operations:**
1. Create API Project
2. Import endpoints via CI/CD (this resets General tab!)
3. Set Base URL in **Provider Dashboard** (NOT Studio Gateway tab)
   - Provider Dashboard → API Specs → Settings → Base URL → Configure "default" pool
4. Configure General tab (descriptions, category, website) — AFTER import
5. Configure Monetization (price dialog + quota dialog separately)
6. Upload logo
7. Set visibility → PUBLIC
8. Copy X-RapidAPI-Proxy-Secret from Gateway tab
9. Add secret to backend env var (comma-separated if multiple listings)
10. **Test through RapidAPI playground** — verify 200 OK with real data

### Multi-Listing Proxy Secret Pattern
When you have multiple RapidAPI listings pointing to the same backend:
1. Each listing generates its own unique X-RapidAPI-Proxy-Secret
2. The backend middleware must accept ALL secrets, not just one
3. Store them comma-separated in a single env var:
   `RAPIDAPI_PROXY_SECRET=secret1,secret2,secret3`
4. Middleware splits by comma and checks `if proxy_secret in valid_secrets`
5. After adding each new listing, copy its proxy secret and append it to the
   Render env var (comma-separated, no spaces)

### Add Proxy Secrets to Render
After getting X-RapidAPI-Proxy-Secret from each listing's Gateway tab:
- Go to Render dashboard → service → Environment
- Set RAPIDAPI_PROXY_SECRET = all secrets comma-separated
- Save (triggers redeploy)

### Pricing Strategy
- Always have generous FREE tier (discovery mechanism)
- Price by buyer persona budget, not by cost
- RapidAPI takes ~25% — plan for that
- Split modules into separate listings when buyer personas differ
- Higher-budget buyers (enterprise, utilities) → higher prices
- Consumer/hobbyist buyers → lower prices, higher volume play

## Phase 7: Custom Domain (5 min)

### Register Domain
- Use Cloudflare Registrar (~$10-12/yr for .dev)
- Navigate to dash.cloudflare.com → Add domain → Register

### Configure DNS on Cloudflare
Add 2 CNAME records:

| Type  | Name | Target                     | Proxy |
|-------|------|----------------------------|-------|
| CNAME | @    | {project}-api.onrender.com | ☁️ On |
| CNAME | www  | {project}-api.onrender.com | ☁️ On |

Cloudflare supports CNAME flattening at root — no A record needed.

### Add Custom Domain on Render
1. Go to Render dashboard → service → Settings
2. Scroll to Custom Domains
3. Add: {project}.dev
4. Add: www.{project}.dev
5. Render auto-verifies DNS and issues SSL certificate

### Verify Domain
- `https://{project}.dev/health` → 200 OK
- `https://www.{project}.dev/health` → 200 OK
- `https://{project}.dev/docs` → Swagger UI

## Phase 8: Post-Launch

### Immediate
- Deploy landing page (dark theme, premium feel, feature cards, pricing, code examples)
- Git push landing page (docs/ directory)

### Week 1
- Monitor RapidAPI Analytics for usage patterns
- Write dev.to article about the API
- Post on relevant subreddits and LinkedIn
- Cross-check data against authoritative sources

### Ongoing
- Add endpoints based on user requests
- Fill in placeholder (501) endpoints
- Add more data tables and calculation types
- Generate SDKs from /openapi.json (openapi-generator-cli)
- Add Stripe direct billing on custom domain

## Reference: TradesCalc Metrics (Benchmark)
- Time from start to live: ~90 minutes
- Endpoints: 25 (12 electrical + 5 utility + 7 fire + 1 system)
- Tests: 33 (all passing)
- Files: 27
- Lines of code: 4,020
- RapidAPI listings: 3 (Electrical, Fire, Utility)
- Pricing tiers: 3-4 per listing
- Logo generation: ~10 seconds each
- Landing page: built by subagent in ~3 minutes
