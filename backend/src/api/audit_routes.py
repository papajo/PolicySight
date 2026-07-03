"""
Audit Trail API Routes (REQ-010)
"""

from fastapi import APIRouter, Query

from src.core.audit import get_audit_log, get_audit_summary, AuditEntry

router = APIRouter()


@router.get("/audit/log")
async def list_audit(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    """Get the chronological audit log. Most recent first."""
    return get_audit_log(limit=limit, offset=offset)


@router.get("/audit/summary")
async def audit_summary():
    """Get audit log summary statistics."""
    return get_audit_summary()
