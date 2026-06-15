from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScheduleCreate(BaseModel):
    schedule_name: str
    department: str
    shift_type: str
    start_time: str
    end_time: str
    grace_time: int = 10
    required_hours: float = 8.0

class ScheduleUpdate(BaseModel):
    schedule_name: Optional[str] = None
    department: Optional[str] = None
    shift_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    grace_time: Optional[int] = None
    required_hours: Optional[float] = None

class ScheduleResponse(BaseModel):
    id: str
    schedule_name: str
    department: str
    shift_type: str
    start_time: str
    end_time: str
    grace_time: int
    required_hours: float
    created_at: datetime