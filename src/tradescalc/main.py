"""
TradesCalc API — Main Application Entry Point.

The Infrastructure API for the Trades.
Built by engineers, for engineers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tradescalc.config import get_settings
from tradescalc.routers import electrical, utility, fire


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup: load NEC data tables into memory
    from tradescalc.services.nec_data import NECDataStore
    NECDataStore.load_all()
    yield
    # Shutdown: cleanup if needed


settings = get_settings()

app = FastAPI(
    title="TradesCalc API",
    description=(
        "**The Infrastructure API for the Trades.**\n\n"
        "NEC-compliant electrical calculations, utility reliability indices, "
        "and fire protection engineering — built by an electrical engineer.\n\n"
        "## API Modules\n\n"
        "- **Electrical** (`/v1/electrical/`) — Wire sizing, voltage drop, conduit fill, "
        "ampacity, breaker sizing, and more. All calculations reference NEC 2023.\n"
        "- **Utility** (`/v1/utility/`) — IEEE 1366 reliability indices (SAIDI, SAIFI, CAIDI), "
        "major event day detection, and outage cost estimation.\n"
        "- **Fire** (`/v1/fire/`) — Hydrant flow, friction loss, pump pressure, "
        "needed fire flow, and ISO grading factors.\n\n"
        "## Authentication\n\n"
        "Include your API key in the `X-Api-Key` header, or use RapidAPI's built-in auth.\n\n"
        "## Disclaimer\n\n"
        "For estimation and planning purposes only. All calculations should be verified "
        "by a licensed professional. Not a substitute for the NEC codebook."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "TradesCalc Support",
        "url": "https://tradescalc.dev",
        "email": "support@tradescalc.dev",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS middleware for direct-domain customers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware: RapidAPI proxy secret validation (production only)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def validate_rapidapi_proxy(request: Request, call_next):
    """Validate RapidAPI proxy secret in production to prevent direct access bypass."""
    if settings.environment == "production" and settings.rapidapi_proxy_secret:
        # Allow health check without auth
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret", "")
        api_key = request.headers.get("X-Api-Key", "")

        # Accept either RapidAPI proxy secret OR direct API key
        if proxy_secret != settings.rapidapi_proxy_secret and not api_key:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Unauthorized",
                    "message": "Valid API key or RapidAPI subscription required.",
                    "docs": "https://tradescalc.dev/docs",
                },
            )

    return await call_next(request)


# ---------------------------------------------------------------------------
# Include API routers
# ---------------------------------------------------------------------------
app.include_router(
    electrical.router,
    prefix="/v1/electrical",
    tags=["Electrical — NEC Calculations"],
)

app.include_router(
    utility.router,
    prefix="/v1/utility",
    tags=["Utility — Reliability Indices"],
)

app.include_router(
    fire.router,
    prefix="/v1/fire",
    tags=["Fire — Protection Engineering"],
)


# ---------------------------------------------------------------------------
# Root & Health endpoints
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint — redirect to docs."""
    return {
        "name": "TradesCalc API",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "operational",
        "modules": {
            "electrical": "/v1/electrical/",
            "utility": "/v1/utility/",
            "fire": "/v1/fire/",
        },
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring and Render."""
    return {"status": "healthy", "version": settings.app_version}
