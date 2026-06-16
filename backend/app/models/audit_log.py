# app/models/audit_log.py
#
# Audit Log model (SRS 9.4 / FIN-10).
# All create, update, delete actions are logged with: user, timestamp,
# action, old value, new value. Read-only; only Super Admin can view it.
# Retained for a minimum of 2 years.

from pydantic import BaseModel
from typing import Optional, Literal, Any
from datetime import datetime

AuditAction = Literal["CREATE", "UPDATE", "DELETE", "APPROVE", "REJECT", "LOGIN", "LOGOUT"]


class AuditLogEntry(BaseModel):
    """Internal representation used when writing a log entry (not exposed via API input)."""
    user_id: str
    user_name: str
    user_role: str
    action: AuditAction
    entity: str          # e.g. "Contract", "Expense", "Employee"
    entity_id: str
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    description: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: str
    log_id: str
    user_id: str
    user_name: str
    user_role: str
    action: str
    entity: str
    entity_id: str
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    description: Optional[str] = None
    timestamp: datetime