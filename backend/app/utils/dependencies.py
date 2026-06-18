# app/utils/dependencies.py
#
# Shared authentication/authorization dependencies used across routes.
# Works purely off the JWT payload's "role" field — not affected by the
# unified login change, since employees are now just another role
# inside the "users" collection.

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
    payload = _decode_token(credentials)
    if payload.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin (CEO) access required")
    return payload


def get_current_hr(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="HR Manager access required")
    return payload


def get_current_finance(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "finance_manager"]:
        raise HTTPException(status_code=403, detail="Finance Manager access required")
    return payload


def get_current_sales_manager(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "sales_manager"]:
        raise HTTPException(status_code=403, detail="Sales Manager access required")
    return payload


def get_current_sales(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "sales_manager", "sales_rep"]:
        raise HTTPException(status_code=403, detail="Sales access required")
    return payload


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "hr_manager", "finance_manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


def get_current_accountant(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = _decode_token(credentials)
    if payload.get("role") not in ["super_admin", "hr_manager", "finance_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return payload