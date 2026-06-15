from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class AttendanceMarkRequest(BaseModel):
    image_base64: str

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

class AttendanceCorrectionRequest(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    reason: str