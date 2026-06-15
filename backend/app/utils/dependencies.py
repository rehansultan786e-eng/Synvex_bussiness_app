# app/utils/dependencies.py
#
# Shared authentication/authorization dependencies used across routes.
#
# Roles per SRS Section 2.2:
# - super_admin     : CEO — full access to everything
# - hr_manager      : HR department head
# - finance_manager : Finance department head
# - sales_manager   : Head of sales team
# - sales_rep       : Individual sales staff
# - employee        : All other staff (handled via separate employee token)

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.auth import verify_token

security = HTTPBearer()


def _decode_token(credentials: HTTPAuthorizationCredentials):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Allows any authenticated user (any role, including employee)."""
    return _decode_token(credentials)


def get_current_super_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Allows: super_admin (CEO) only."""
    payload = _decode_token(credentials)
    if payload.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin (CEO) access required")
    return payload


def get_current_hr(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Allows: super_admin, hr_manager — used for HR/employee/attendance/leave/asset management."""
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="HR Manager access required")
    return payload


def get_current_finance(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Allows: super_admin, finance_manager — used for contracts/invoices/expenses/payroll."""
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "finance_manager"]:
        raise HTTPException(status_code=403, detail="Finance Manager access required")
    return payload


def get_current_sales_manager(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Allows: super_admin, sales_manager — used for team-wide sales reports."""
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "sales_manager"]:
        raise HTTPException(status_code=403, detail="Sales Manager access required")
    return payload


def get_current_sales(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Allows: super_admin, sales_manager, sales_rep — used for lead/commission access."""
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "sales_manager", "sales_rep"]:
        raise HTTPException(status_code=403, detail="Sales access required")
    return payload


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Allows: super_admin, hr_manager, finance_manager
    General "admin-level" access for legacy attendance/department/schedule routes.
    """
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "hr_manager", "finance_manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


def get_current_accountant(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Allows: super_admin, hr_manager, finance_manager
    General "report viewing" access for legacy attendance/leave/analytics routes.
    """
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "hr_manager", "finance_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return payload