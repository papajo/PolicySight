"""
PolicySight — AI-Driven Auto Insurance Middleware
Main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Your Policy, Decoded. Your Claim, Defended.",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name, "env": settings.app_env}


# Import and include routers
from src.api.policy_routes import router as policy_router
from src.api.claims_routes import router as claims_router
from src.api.rate_routes import router as rate_router

app.include_router(policy_router, prefix="/api/policies", tags=["Policies"])
app.include_router(claims_router, prefix="/api/claims", tags=["Claims"])
app.include_router(rate_router, prefix="/api/rates", tags=["Rates"])