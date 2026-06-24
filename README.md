# TradesCalc API ⚡🔧🔥

**The Infrastructure API for the Trades.**

NEC-compliant electrical calculations, utility reliability indices, and fire protection engineering — built by a licensed electrical engineer.

## API Modules

### ⚡ Electrical (`/v1/electrical/`)
Wire sizing, voltage drop, conduit fill, ampacity, breaker sizing, transformer sizing, and more. All calculations reference NEC 2023.

### 📊 Utility (`/v1/utility/`)
IEEE 1366 reliability indices (SAIDI, SAIFI, CAIDI), major event day detection, and outage cost estimation.

### 🔥 Fire (`/v1/fire/`)
Hydrant flow, friction loss, pump pressure, needed fire flow, ISO grading factors, and NERIS code reference.

## Quick Start

```bash
# Clone and install
git clone https://github.com/tradescalc/tradescalc-api.git
cd tradescalc-api
pip install -e ".[dev]"

# Run locally
uvicorn src.tradescalc.main:app --reload

# Open docs
# http://localhost:8000/docs
```

## Example Request

```bash
curl -X POST http://localhost:8000/v1/electrical/voltage-drop \
  -H "Content-Type: application/json" \
  -d '{
    "load_amps": 20,
    "distance_ft": 100,
    "wire_size": "12",
    "voltage": 120,
    "phase": "single",
    "material": "copper"
  }'
```

## Running Tests

```bash
pytest tests/ -v
```

## Deployment

Configured for auto-deploy to [Render](https://render.com) via `render.yaml`. Push to `main` to deploy.

## Tech Stack

- **Python 3.12** + **FastAPI** + **Pydantic v2**
- **Uvicorn** ASGI server
- **Render** for hosting
- **RapidAPI** for marketplace distribution

## Disclaimer

For estimation and planning purposes only. All calculations should be verified by a licensed professional. Not a substitute for the NEC codebook.

## License

MIT
