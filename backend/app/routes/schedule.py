from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schedule import ScheduleCreate, ScheduleUpdate
from app.services.schedule import (
    create_schedule, get_all_schedules,
    get_schedule_by_id, update_schedule, delete_schedule
)
from app.utils.auth import verify_token
from typing import Optional

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])
security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload

@router.post("/", status_code=201)
async def create_new_schedule(
    schedule_data: ScheduleCreate,
    admin=Depends(get_current_admin)
):
    schedule, error = await create_schedule(schedule_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Schedule created successfully", "data": schedule}

@router.get("/")
async def get_schedules(
    department: Optional[str] = Query(None),
    shift_type: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    schedules = await get_all_schedules(department, shift_type)
    return {"message": "Success", "data": schedules, "total": len(schedules)}

@router.get("/{schedule_id}")
async def get_schedule(schedule_id: str, admin=Depends(get_current_admin)):
    schedule = await get_schedule_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Success", "data": schedule}

@router.put("/{schedule_id}")
async def update_existing_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    admin=Depends(get_current_admin)
):
    schedule = await update_schedule(schedule_id, schedule_data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule updated successfully", "data": schedule}

@router.delete("/{schedule_id}")
async def delete_existing_schedule(schedule_id: str, admin=Depends(get_current_admin)):
    await delete_schedule(schedule_id)
    return {"message": "Schedule deleted successfully"}