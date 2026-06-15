from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LeaveRequest(BaseModel):
    employee_id: str
    leave_date: str
    leave_type: str
    reason: str

class LeaveUpdate(BaseModel):
    status: str
    admin_comment: Optional[str] = None

class LeaveResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    leave_date: str
    leave_type: str
    reason: str
    status: str
    admin_comment: Optional[str]
    created_at: datetime