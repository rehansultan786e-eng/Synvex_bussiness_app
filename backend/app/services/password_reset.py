# app/services/password_reset.py
#
# Password reset service (SRS 9.1).
# Works for both manager-role users (in "users" collection) and
# employees (in "employees" collection) — detected by email lookup.

from app.database.connection import get_db
from app.utils.auth import hash_password, create_invite_token, verify_invite_token
from app.utils.password_policy import validate_password_strength
from datetime import datetime, timedelta
from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
RESET_TOKEN_EXPIRE_MINUTES = 15


def _create_reset_token(account_type: str, identifier: str, email: str) -> str:
    to_encode = {
        "account_type": account_type,  # "user" or "employee"
        "identifier": identifier,       # user_id or employee_id
        "email": email,
        "type": "password_reset"
    }
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload
    except Exception:
        return None


async def request_password_reset(email: str):
    """
    SRS 9.1: Sends a secure password reset link valid for 15 minutes.
    Always returns success-style response (no account enumeration),
    but only actually sends an email if the account exists.
    """
    db = get_db()

    user = await db.users.find_one({"email": email})
    employee = None
    if not user:
        employee = await db.employees.find_one({"email": email, "is_deleted": False})

    if not user and not employee:
        # Don't reveal whether the email exists
        return True

    if user:
        token = _create_reset_token("user", str(user["_id"]), email)
        name = user["full_name"]
    else:
        token = _create_reset_token("employee", employee["employee_id"], email)
        name = employee["full_name"]

    await _send_reset_email(email, name, token)
    return True


async def _send_reset_email(to_email: str, full_name: str, token: str):
    from app.utils.email_service import FRONTEND_BASE_URL, send_email

    reset_link = f"{FRONTEND_BASE_URL}/reset-password?token={token}"
    subject = "Reset Your Password - Synvex"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">
        <h2>Password Reset Request</h2>
        <p>Hi {full_name},</p>
        <p>We received a request to reset your password. Click the button below to set a new password:</p>
        <p>
            <a href="{reset_link}"
               style="background:#2563eb;color:#fff;padding:10px 20px;
                      text-decoration:none;border-radius:6px;display:inline-block;">
                Reset Password
            </a>
        </p>
        <p>This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes. If you did not request this, please ignore this email.</p>
    </div>
    """
    send_email(to_email, subject, html_body)


async def reset_password_with_token(token: str, new_password: str):
    payload = _verify_reset_token(token)
    if not payload:
        return False, "Invalid or expired reset link"

    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        return False, error_msg

    db = get_db()
    hashed = hash_password(new_password)

    if payload["account_type"] == "user":
        from bson import ObjectId
        result = await db.users.update_one(
            {"_id": ObjectId(payload["identifier"])},
            {"$set": {"password": hashed, "updated_at": datetime.utcnow()}}
        )
    else:
        result = await db.employees.update_one(
            {"employee_id": payload["identifier"]},
            {"$set": {"password": hashed, "updated_at": datetime.utcnow()}}
        )

    if result.matched_count == 0:
        return False, "Account not found"

    return True, None