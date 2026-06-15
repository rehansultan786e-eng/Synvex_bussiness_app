# app/models/user.py
#
# User roles per SRS Section 2.2:
# - super_admin   : CEO / company owner — full access
# - hr_manager    : HR department head
# - finance_manager : Finance department head
# - sales_manager : Head of sales team
# - sales_rep     : Individual sales staff
# (employee role is handled separately in the "employees" collection)

from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime

# Roles creatable via invite system (employee handled separately)
UserRole = Literal["super_admin", "hr_manager", "finance_manager", "sales_manager", "sales_rep"]

# ===== EXISTING MODELS =====

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ===== Invite-based account creation =====

class InviteUserRequest(BaseModel):
    full_name: str
    email: EmailStr
    role: UserRole


class InviteUserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    is_active: bool
    invite_sent: bool


class SetPasswordRequest(BaseModel):
    token: str
    password: str


class ResendInviteRequest(BaseModel):
    user_id: str