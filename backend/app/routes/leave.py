from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.leave import LeaveRequest, LeaveUpdate
from app.services.leave import (
    create_leave_request, get_all_leave_requests,
    get_employee_leave_requests, update_leave_status
)
from app.utils.auth import verify_token
from typing import Optional

router = APIRouter(prefix="/api/leaves", tags=["Leave Management"])
security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.post("/", status_code=201)
async def submit_leave_request(leave_data: LeaveRequest):
    leave, error = await create_leave_request(leave_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Leave request submitted successfully", "data": leave}

@router.get("/")
async def get_leaves(
    status: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    leaves = await get_all_leave_requests(status)
    return {"message": "Success", "data": leaves, "total": len(leaves)}

@router.get("/employee/{employee_id}")
async def get_employee_leaves(employee_id: str):
    leaves = await get_employee_leave_requests(employee_id)
    return {"message": "Success", "data": leaves}

@router.put("/{leave_id}")
async def update_leave(
    leave_id: str,
    leave_update: LeaveUpdate,
    admin=Depends(get_current_admin)
):
    leave, error = await update_leave_status(leave_id, leave_update)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": f"Leave {leave_update.status} successfully", "data": leave}