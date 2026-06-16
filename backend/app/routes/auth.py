# app/routes/auth.py
#
# Authentication routes.
#
# SRS 9.1: Login for super_admin and finance_manager now requires 2FA
# (email OTP). Flow:
#   1. POST /login -> if 2FA required, returns {"requires_2fa": true, "temp_token": ...}
#                      (no access/refresh tokens yet)
#                   -> if 2FA not required, returns normal TokenResponse directly
#   2. POST /verify-2fa -> temp_token + otp -> returns TokenResponse
#   3. POST /resend-2fa -> temp_token -> resends OTP (rate-limited)
#
# Invite permission rules (who can invite whom):
# - super_admin (CEO)   -> can invite anyone: hr_manager, finance_manager,
#                          sales_manager, sales_rep
# - sales_manager        -> can invite: sales_rep

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import (
    UserLogin, TokenResponse,
    InviteUserRequest, InviteUserResponse,
    SetPasswordRequest, ResendInviteRequest
)
from app.models.two_factor import TwoFactorVerifyRequest, TwoFactorResendRequest
from app.database.connection import get_db
from app.utils.auth import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.utils.dependencies import get_current_user
from app.services.user import (
    create_invited_user, set_user_password_via_invite,
    resend_invite, get_all_users, get_user_by_email
)
from app.services.two_factor import (
    create_2fa_challenge, verify_otp, resend_otp, requires_2fa
)
from app.models.password_reset import ForgotPasswordRequest, ResetPasswordRequest
from app.services.password_reset import request_password_reset, reset_password_with_token
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

class EmployeeLoginRequest(BaseModel):
    employee_id: str
    password: str


# ===== LOGIN (2FA-aware) =====

@router.post("/login")
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

    role = user["role"]

    if requires_2fa(role):
        temp_token = await create_2fa_challenge(str(user["_id"]), user["email"], role)
        return {
            "requires_2fa": True,
            "temp_token": temp_token,
            "message": "A verification code has been sent to your email."
        }

    token_data = {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": role
    }
    return {
        "requires_2fa": False,
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer"
    }


@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa_route(request: TwoFactorVerifyRequest):
    """SRS 9.1: Completes login for super_admin/finance_manager after OTP verification."""
    user_payload, error = await verify_otp(request.temp_token, request.otp)
    if error:
        raise HTTPException(status_code=400, detail=error)

    token_data = {
        "user_id": user_payload["user_id"],
        "email": user_payload["email"],
        "role": user_payload["role"]
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data)
    )


@router.post("/resend-2fa")
async def resend_2fa_route(request: TwoFactorResendRequest):
    new_temp_token, error = await resend_otp(request.temp_token)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"temp_token": new_temp_token, "message": "A new verification code has been sent to your email."}


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
    requester_role = current_user.get("role")

    if requester_role == "super_admin":
        pass
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
    
    # ===== PASSWORD RESET (SRS 9.1) =====

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    await request_password_reset(request.email)
    return {"message": "If an account exists with this email, a password reset link has been sent."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    success, error = await reset_password_with_token(request.token, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Password reset successfully. You can now log in with your new password."}