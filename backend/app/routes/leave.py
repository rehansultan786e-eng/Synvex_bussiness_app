# app/routes/leave.py
#
# Leave routes (SRS 6.4). Updated to match the rewritten leave model
# (multi-day from_date/to_date, leave types with quotas) and service
# (balance checking/deduction, reporting-manager notification flow).

from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.leave import LeaveRequestCreate, LeaveUpdate
from app.services.leave import (
    create_leave_request, get_all_leave_requests,
    get_employee_leave_requests, update_leave_status,
    cancel_leave_request
)
from app.services.leave_balance import get_leave_balance
from app.utils.dependencies import get_current_user, get_current_accountant
from typing import Optional

router = APIRouter(prefix="/api/leaves", tags=["Leave Management"])


@router.post("/", status_code=201)
async def submit_leave_request(leave_data: LeaveRequestCreate):
    """Employee submits a leave request (SRS 6.4.2 step 1)."""
    leave, error = await create_leave_request(leave_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Leave request submitted successfully", "data": leave}


@router.get("/")
async def get_leaves(
    status: Optional[str] = Query(None),
    leave_type: Optional[str] = Query(None),
    admin=Depends(get_current_accountant)
):
    """HR Manager / Finance Manager / CEO view: all leave requests."""
    leaves = await get_all_leave_requests(status=status, leave_type=leave_type)
    return {"message": "Success", "data": leaves, "total": len(leaves)}


@router.get("/employee/{employee_id}")
async def get_employee_leaves(employee_id: str):
    """Employee self-service: own leave request history."""
    leaves = await get_employee_leave_requests(employee_id)
    return {"message": "Success", "data": leaves}


@router.get("/balance/{employee_id}")
async def get_employee_leave_balance(
    employee_id: str,
    year: Optional[int] = Query(None)
):
    """SRS 6.5 self-service: check leave balance (Annual/Sick/Casual/etc.)."""
    balance = await get_leave_balance(employee_id, year)
    return {"message": "Success", "data": balance}


@router.put("/{leave_id}")
async def update_leave(
    leave_id: str,
    leave_update: LeaveUpdate,
    current_user=Depends(get_current_user)
):
    """
    Reporting Manager / HR Manager / CEO approves or rejects a leave request
    (SRS 6.4.2 steps 2-5). Approval deducts leave balance and marks
    attendance as 'on_leave' for each day in the range.
    """
    if current_user.get("role") not in ["super_admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Only HR Manager or CEO can approve/reject leave requests")

    leave, error = await update_leave_status(
        leave_id, leave_update,
        approved_by=current_user.get("user_id")
    )
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": f"Leave {leave_update.status} successfully", "data": leave}


@router.put("/{leave_id}/cancel")
async def cancel_leave(leave_id: str, employee_id: str):
    """Employee cancels their own pending or approved leave request."""
    leave, error = await cancel_leave_request(leave_id, employee_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Leave request cancelled successfully", "data": leave}