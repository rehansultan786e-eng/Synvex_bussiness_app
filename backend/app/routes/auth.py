# app/routes/auth.py
#
# Authentication routes.
#
# Invite permission rules (who can invite whom):
# - super_admin (CEO)   -> can invite anyone: hr_manager, finance_manager,
#                          sales_manager, sales_rep
# - hr_manager           -> can invite: sales_rep (rare) - mainly manages employees
#                          via the employee module (separate from user invites)
# - sales_manager        -> can invite: sales_rep
#
# - /login            : manager-level login (super_admin, hr_manager,
#                        finance_manager, sales_manager, sales_rep)
# - /employee-login   : employee login (unchanged)
# - /me               : returns current logged-in user info
# - /invite-user      : invite a new manager/rep user
# - /set-password     : activate account via invite link
# - /resend-invite    : resend invite email
# - /users            : list users

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import (
    UserLogin, TokenResponse,
    InviteUserRequest, InviteUserResponse,
    SetPasswordRequest, ResendInviteRequest
)
from app.database.connection import get_db
from app.utils.auth import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.utils.dependencies import get_current_user
from app.services.user import (
    create_invited_user, set_user_password_via_invite,
    resend_invite, get_all_users, get_user_by_email
)
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

class EmployeeLoginRequest(BaseModel):
    employee_id: str
    password: str


# ===== LOGIN =====

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": credentials.email})

    if not user or not verify_password(credentials.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=403,
            detail="Account not activated. Please check your email to set your password."
        )

    token_data = {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"]
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data)
    )


# ===== EMPLOYEE LOGIN (unchanged) =====

@router.post("/employee-login")
async def employee_login(credentials: EmployeeLoginRequest):
    db = get_db()
    employee = await db.employees.find_one({
        "employee_id": credentials.employee_id,
        "is_deleted": False,
        "status": "active"
    })
    if not employee:
        raise HTTPException(status_code=401, detail="Employee ID not found or inactive")

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    if not pwd_context.verify(credentials.password, employee.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid password")

    token_data = {
        "employee_id": employee["employee_id"],
        "full_name": employee["full_name"],
        "department": employee["department"],
        "role": "employee"
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "role": "employee",
        "employee": {
            "employee_id": employee["employee_id"],
            "full_name": employee["full_name"],
            "department": employee["department"],
            "designation": employee["designation"]
        }
    }


# ===== ME =====

@router.get("/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    db = get_db()

    role = payload.get("role")

    if role == "employee":
        employee = await db.employees.find_one({"employee_id": payload["employee_id"]})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {
            "employee_id": employee["employee_id"],
            "full_name": employee["full_name"],
            "department": employee["department"],
            "role": "employee"
        }
    else:
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(payload["user_id"])})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": str(user["_id"]),
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"]
        }


# ===== INVITE A NEW USER =====

@router.post("/invite-user", response_model=InviteUserResponse)
async def invite_user(request: InviteUserRequest, current_user=Depends(get_current_user)):
    """
    Permission rules:
    - super_admin (CEO) can invite: hr_manager, finance_manager, sales_manager, sales_rep
    - sales_manager can invite: sales_rep only
    - hr_manager / finance_manager / sales_rep cannot invite anyone
    """
    requester_role = current_user.get("role")

    if requester_role == "super_admin":
        pass  # can invite any role
    elif requester_role == "sales_manager":
        if request.role != "sales_rep":
            raise HTTPException(status_code=403, detail="Sales Manager can only invite Sales Reps")
    else:
        raise HTTPException(status_code=403, detail="You do not have permission to invite users")

    if request.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot create another super admin via invite")

    created_user, invite_sent = await create_invited_user(
        full_name=request.full_name,
        email=request.email,
        role=request.role,
        created_by=current_user.get("user_id")
    )

    if created_user is None:
        raise HTTPException(status_code=400, detail=invite_sent)

    return InviteUserResponse(
        id=created_user["id"],
        full_name=created_user["full_name"],
        email=created_user["email"],
        role=created_user["role"],
        is_active=created_user["is_active"],
        invite_sent=invite_sent
    )


# ===== SET PASSWORD VIA INVITE =====

@router.post("/set-password")
async def set_password(request: SetPasswordRequest):
    success, error = await set_user_password_via_invite(request.token, request.password)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Password set successfully. You can now log in."}


# ===== RESEND INVITE =====

@router.post("/resend-invite")
async def resend_invite_route(request: ResendInviteRequest, current_user=Depends(get_current_user)):
    if current_user.get("role") not in ["super_admin", "sales_manager"]:
        raise HTTPException(status_code=403, detail="You do not have permission to resend invites")

    invite_sent, error = await resend_invite(request.user_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Invite email resent", "invite_sent": invite_sent}


# ===== LIST USERS =====

@router.get("/users")
async def list_users(current_user=Depends(get_current_user)):
    """
    super_admin: sees all manager/rep users
    sales_manager: sees sales_rep users only
    others: forbidden
    """
    role = current_user.get("role")

    if role == "super_admin":
        all_users = []
        for r in ["hr_manager", "finance_manager", "sales_manager", "sales_rep"]:
            all_users += await get_all_users(r)
        return {"users": all_users}
    elif role == "sales_manager":
        return {"users": await get_all_users("sales_rep")}
    else:
        raise HTTPException(status_code=403, detail="You do not have permission to view users")