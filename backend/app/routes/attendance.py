# app/routes/attendance.py
#
# Attendance marking and reporting routes (SRS 6.3).
#
# The "/mark" endpoint remains public (used by employee face check-in).
# NEW: manual override (after 3 failed face attempts), monthly summary,
# and an absent-auto-marking trigger endpoint (run once daily via cron/HR).

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from app.models.attendance import AttendanceCorrectionRequest, ManualOverrideRequest
from app.services.attendance import (
    mark_attendance, get_attendance_by_date,
    get_employee_attendance_history, correct_attendance,
    manual_override_attendance, auto_mark_absentees,
    get_monthly_attendance_summary
)
from app.utils.dependencies import get_current_accountant, get_current_hr
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

class AttendanceMarkRequest(BaseModel):
    image_base64: str
    mode: str = "checkin"


def _extract_client_ip(request: Request) -> str:
    client_ip = request.headers.get("X-Forwarded-For")
    if not client_ip:
        client_ip = request.headers.get("X-Real-IP")
    if not client_ip:
        client_ip = request.client.host
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    return client_ip


@router.post("/mark")
async def mark_employee_attendance(request: Request, data: AttendanceMarkRequest):
    import httpx
    client_ip = _extract_client_ip(request)

    if client_ip in ["127.0.0.1", "::1", "localhost"]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.ipify.org?format=json", timeout=5)
                client_ip = response.json()["ip"]
        except:
            pass

    from app.services.ip_settings import verify_ip
    is_allowed, message = await verify_ip(client_ip)
    if not is_allowed:
        raise HTTPException(status_code=403, detail=message)

    device_info = request.headers.get("User-Agent", "Unknown device")

    attendance, error = await mark_attendance(
        data.image_base64, data.mode,
        ip_address=client_ip, device_info=device_info
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Attendance marked successfully", "data": attendance}


@router.post("/manual-override")
async def manual_override_route(
    request: ManualOverrideRequest,
    current_user=Depends(get_current_hr)
):
    """
    SRS 6.3.2: After 3 failed face-match attempts, HR Manager manually
    marks check-in/check-out with a reason.
    """
    attendance, error = await manual_override_attendance(
        request.employee_id, request.mode, request.reason,
        marked_by=current_user.get("user_id")
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Attendance manually marked successfully", "data": attendance}


@router.post("/run-absent-marking")
async def run_absent_marking(current_user=Depends(get_current_hr)):
    """
    SRS 6.3.2: Marks 'absent' for all active employees with no attendance
    record for today. Intended to run once at end-of-day (manually by HR,
    or via an external scheduler/cron hitting this endpoint).
    """
    marked_count = await auto_mark_absentees()
    return {"message": f"{marked_count} employees marked as absent for today", "marked_count": marked_count}


@router.get("/today")
async def get_today_attendance(
    department: Optional[str] = Query(None),
    admin=Depends(get_current_accountant)
):
    from datetime import date
    today = str(date.today())
    records = await get_attendance_by_date(today, department)
    return {"message": "Success", "data": records, "total": len(records)}


@router.get("/date/{date_str}")
async def get_attendance_by_specific_date(
    date_str: str,
    department: Optional[str] = Query(None),
    admin=Depends(get_current_accountant)
):
    records = await get_attendance_by_date(date_str, department)
    return {"message": "Success", "data": records, "total": len(records)}


@router.get("/employee/{employee_id}")
async def get_employee_history(
    employee_id: str,
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    admin=Depends(get_current_accountant)
):
    records = await get_employee_attendance_history(employee_id, month, year)
    return {"message": "Success", "data": records, "total": len(records)}


@router.get("/employee/{employee_id}/summary")
async def get_employee_monthly_summary(
    employee_id: str,
    month: int = Query(...),
    year: int = Query(...),
    admin=Depends(get_current_accountant)
):
    """SRS 6.3.3: Monthly attendance summary (days present, absent, late)."""
    summary = await get_monthly_attendance_summary(employee_id, month, year)
    return {"message": "Success", "data": summary}


@router.post("/correct")
async def correct_employee_attendance(
    correction: AttendanceCorrectionRequest,
    admin=Depends(get_current_accountant)
):
    await correct_attendance(correction)
    return {"message": "Attendance corrected successfully"}