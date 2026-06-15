from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.attendance import AttendanceCorrectionRequest
from app.services.attendance import (
    mark_attendance, get_attendance_by_date,
    get_employee_attendance_history, correct_attendance
)
from app.utils.auth import verify_token
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
security = HTTPBearer()

class AttendanceMarkRequest(BaseModel):
    image_base64: str
    mode: str = "checkin"

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.post("/mark")
async def mark_employee_attendance(request: AttendanceMarkRequest):
    attendance, error = await mark_attendance(request.image_base64, request.mode)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Attendance marked successfully", "data": attendance}

@router.get("/today")
async def get_today_attendance(
    department: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    from datetime import date
    today = str(date.today())
    records = await get_attendance_by_date(today, department)
    return {"message": "Success", "data": records, "total": len(records)}

@router.get("/date/{date_str}")
async def get_attendance_by_specific_date(
    date_str: str,
    department: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    records = await get_attendance_by_date(date_str, department)
    return {"message": "Success", "data": records, "total": len(records)}

@router.get("/employee/{employee_id}")
async def get_employee_history(
    employee_id: str,
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    admin=Depends(get_current_admin)
):
    records = await get_employee_attendance_history(employee_id, month, year)
    return {"message": "Success", "data": records, "total": len(records)}

@router.post("/correct")
async def correct_employee_attendance(
    correction: AttendanceCorrectionRequest,
    admin=Depends(get_current_admin)
):
    await correct_attendance(correction)
    return {"message": "Attendance corrected successfully"}