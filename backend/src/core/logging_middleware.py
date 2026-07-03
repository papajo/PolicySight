"""
Logging & Production Hardening Middleware
Adds request logging, rate limiting headers, and security headers.
"""

import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("policysight.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests with duration and status."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} "
            f"({duration*1000:.0f}ms)"
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Rate limit tracking middleware.
    In production, use a proper rate limiter (e.g., slowapi).
    This provides headers but doesn't enforce limits.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Placeholder rate limit headers
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = "99"
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 3600))

        return response