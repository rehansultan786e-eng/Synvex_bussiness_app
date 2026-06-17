from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models.leave import LeaveRequestCreate, LeaveUpdate, LeaveResponse, LeaveBalanceResponse
from app.services.leave import (
    create_leave_request,
    update_leave_status,
    cancel_leave_request,
    get_all_leave_requests,
    get_employee_leave_requests
)
from app.services.leave_balance import get_leave_balance
from app.utils.dependencies import (
    get_current_user,
    get_current_admin  # Alias covering super_admin, hr_manager, finance_manager
)

router = APIRouter(prefix="/api/leaves", tags=["Leave Management"])


@router.post("/", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
async def create_new_leave(
    leave_data: LeaveRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a new multi-day leave request.
    Validates balance sufficiency and checks for overlapping dates automatically.
    """
    # RBAC: Regular employees can only submit leave requests for their own employee_id
    if current_user.get("role") == "employee" and leave_data.employee_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only authorized to submit leave requests for yourself."
        )
    
    result, error = await create_leave_request(leave_data)
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    return result


@router.get("/balance/{employee_id}", response_model=LeaveBalanceResponse)
async def get_employee_balance(
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch running leave balances (Allocated, Used, Remaining) for a specific employee.
    """
    # RBAC: Employees can only view their own leave balances
    if current_user.get("role") == "employee" and employee_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only authorized to view your own leave balance."
        )
        
    balance = await get_leave_balance(employee_id)
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave balance record not found for this employee."
        )
    return balance


@router.get("/my-requests", response_model=List[LeaveResponse])
async def get_my_leaves(current_user: dict = Depends(get_current_user)):
    """
    Retrieve all leave requests submitted by the currently logged-in employee.
    """
    return await get_employee_leave_requests(current_user.get("user_id"))


@router.get("/", response_model=List[LeaveResponse])
async def get_all_leaves(
    status_filter: Optional[str] = None,
    leave_type: Optional[str] = None,
    current_user: dict = Depends(get_current_admin)
):
    """
    Admin/Management endpoint to view all company-wide leave requests.
    Supports structural filtering via query parameters.
    """
    return await get_all_leave_requests(status=status_filter, leave_type=leave_type)


@router.put("/{leave_id}/status", response_model=LeaveResponse)
async def change_leave_status(
    leave_id: str,
    leave_update: LeaveUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Approve or Reject a pending leave request.
    Triggers ledger balancing adjustments and populates attendance registries upon approval.
    """
    # Validation: Managers/Admins handle requests. If additional strict rule checks are 
    # handled inside the business workflow service layer, we safely extract user identity here.
    approved_by = current_user.get("user_id")
    
    result, error = await update_leave_status(leave_id, leave_update, approved_by)
    if error:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in error.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=error
        )
    return result


@router.post("/{leave_id}/cancel", response_model=LeaveResponse)
async def cancel_leave(
    leave_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel an approved or pending leave request.
    Restores the leave balances and automatically purges system-generated attendance blocks.
    """
    employee_id = current_user.get("user_id")
    
    result, error = await cancel_leave_request(leave_id, employee_id)
    if error:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in error.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=error
        )
    return result