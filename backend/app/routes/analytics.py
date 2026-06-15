from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.analytics import (
    get_dashboard_stats, get_monthly_attendance_trend,
    get_department_attendance_stats
)
from app.utils.auth import verify_token
from datetime import date

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.get("/dashboard")
async def dashboard_stats(admin=Depends(get_current_admin)):
    stats = await get_dashboard_stats()
    return {"message": "Success", "data": stats}

@router.get("/monthly-trend")
async def monthly_trend(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month),
    admin=Depends(get_current_admin)
):
    data = await get_monthly_attendance_trend(year, month)
    return {"message": "Success", "data": data}

@router.get("/department-stats")
async def department_stats(admin=Depends(get_current_admin)):
    data = await get_department_attendance_stats()
    return {"message": "Success", "data": data}