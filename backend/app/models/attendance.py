# app/models/attendance.py
#
# Attendance model (SRS 6.3).
# Status values: present, late, half_day, absent, on_leave.
# Records now capture IP address and device info (SRS 6.3.2),
# and track failed face-match attempts for manual override flow.

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date

AttendanceStatus = Literal["present", "late", "half_day", "absent", "on_leave"]


class AttendanceMarkRequest(BaseModel):
    image_base64: str


class ManualOverrideRequest(BaseModel):
    """HR Manager manually marks attendance after 3 failed face-match attempts (SRS 6.3.2)."""
    employee_id: str
    mode: Literal["checkin", "checkout"]
    reason: str


class AttendanceResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    department: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    work_hours: Optional[float] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    manual_override: bool = False
    override_reason: Optional[str] = None
    corrected: bool = False


class AttendanceCorrectionRequest(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    reason: str