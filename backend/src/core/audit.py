"""
Audit Trail (REQ-010)
Chronological logging of all system actions.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class AuditEntry(BaseModel):
    id: int
    timestamp: str
    action: str
    resource: str
    user: str = "demo@demo.com"
    details: str = ""
    severity: str = "info"  # info, warning, error


_audit_log: list[AuditEntry] = []
_next_id: int = 1


def log_action(
    action: str,
    resource: str,
    details: str = "",
    user: str = "demo@demo.com",
    severity: str = "info",
) -> AuditEntry:
    global _next_id
    entry = AuditEntry(
        id=_next_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        action=action,
        resource=resource,
        user=user,
        details=details,
        severity=severity,
    )
    _audit_log.append(entry)
    _next_id += 1
    return entry


def get_audit_log(limit: int = 100, offset: int = 0) -> list[AuditEntry]:
    return list(reversed(_audit_log))[offset:offset + limit]


def get_audit_summary() -> dict:
    total = len(_audit_log)
    by_action: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for entry in _audit_log:
        by_action[entry.action] = by_action.get(entry.action, 0) + 1
        by_severity[entry.severity] = by_severity.get(entry.severity, 0) + 1
    return {
        "total_entries": total,
        "by_action": by_action,
        "by_severity": by_severity,
    }


def clear_log() -> None:
    _audit_log.clear()
