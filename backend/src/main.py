"""
PolicySight — AI-Driven Auto Insurance Middleware
Main application entry point.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.core.logging_middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitHeadersMiddleware,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("policysight")

settings = get_settings()

from src.db.seed import seed_demo_user

app = FastAPI(
    title=settings.app_name,
    description="Your Policy, Decoded. Your Claim, Defended.",
    version="0.1.0",
)

# Middleware stack (order matters: first added = last executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Ensure demo user exists on startup."""
    seed_demo_user()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name, "env": settings.app_env}


# Import and include routers
from src.api.policy_routes import router as policy_router
from src.api.claims_routes import router as claims_router
from src.api.rate_routes import router as rate_router
from src.api.lapse_routes import router as lapse_router
from src.api.auth_routes import router as auth_router
from src.api.timeline_routes import router as timeline_router
from src.api.audit_routes import router as audit_router

app.include_router(policy_router, prefix="/api/policies", tags=["Policies"])
app.include_router(claims_router, prefix="/api/claims", tags=["Claims"])
app.include_router(rate_router, prefix="/api/rates", tags=["Rates"])
app.include_router(lapse_router, prefix="/api/lapse", tags=["Lapse Bridge"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(timeline_router, prefix="/api", tags=["Timeline"])
app.include_router(audit_router, prefix="/api", tags=["Audit"])
