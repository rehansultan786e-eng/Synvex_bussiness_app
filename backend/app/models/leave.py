# app/models/leave.py
#
# Leave model (SRS 6.4).
#
# Leave Types & default annual quotas (SRS 6.4.1):
# - Annual Leave: 15 days/year
# - Sick Leave: 10 days/year
# - Casual Leave: 5 days/year
# - Unpaid Leave: no quota limit
# - Maternity / Paternity Leave: handled case-by-case (no fixed default quota here)
#
# Leave requests now support multi-day ranges (from_date -> to_date)
# instead of a single leave_date.

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date

LeaveType = Literal["Annual", "Sick", "Casual", "Unpaid", "Maternity", "Paternity"]
LeaveStatus = Literal["pending", "approved", "rejected", "cancelled"]

# Default annual quotas in days (configurable per company policy)
DEFAULT_LEAVE_QUOTAS = {
    "Annual": 15,
    "Sick": 10,
    "Casual": 5,
    "Unpaid": None,     # unlimited, but unpaid
    "Maternity": 90,
    "Paternity": 14
}


class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: LeaveType
    from_date: date
    to_date: date
    reason: str


class LeaveUpdate(BaseModel):
    status: LeaveStatus
    admin_comment: Optional[str] = None


class LeaveResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    leave_type: str
    from_date: str
    to_date: str
    total_days: int
    reason: str
    status: str
    admin_comment: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class LeaveBalanceResponse(BaseModel):
    employee_id: str
    year: int
    balances: dict   # e.g. {"Annual": {"quota": 15, "used": 3, "remaining": 12}, ...}