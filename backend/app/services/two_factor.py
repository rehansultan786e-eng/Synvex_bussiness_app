# app/services/two_factor.py
#
# 2FA service (SRS 9.1): email OTP, mandatory for super_admin and finance_manager.
#
# Login flow for these roles becomes two-step:
# 1. POST /api/auth/login -> password verified -> OTP emailed -> returns temp_token
#    (NOT a full access token)
# 2. POST /api/auth/verify-2fa -> OTP + temp_token -> returns real access/refresh tokens
#
# OTP is stored hashed, expires in 5 minutes, max 5 attempts, resend rate-limited.

import random
import string
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.utils.auth import hash_password, verify_password, create_access_token

ROLES_REQUIRING_2FA = ["super_admin", "finance_manager"]
OTP_EXPIRY_MINUTES = 5
OTP_RESEND_COOLDOWN_SECONDS = 30
MAX_OTP_ATTEMPTS = 5


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


async def create_2fa_challenge(user_id: str, email: str, role: str):
    """
    Called after password is verified for a 2FA-required role.
    Generates OTP, emails it, and returns a short-lived temp_token
    that the client must present along with the OTP to complete login.
    """
    db = get_db()
    otp = generate_otp()
    otp_hash = hash_password(otp)

    temp_token = create_access_token(
        {"user_id": user_id, "email": email, "role": role, "purpose": "2fa_pending"},
        expires_delta=timedelta(minutes=OTP_EXPIRY_MINUTES)
    )

    await db.two_factor_challenges.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "email": email,
            "otp_hash": otp_hash,
            "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            "attempts": 0,
            "last_sent_at": datetime.utcnow()
        }},
        upsert=True
    )

    await _send_otp_email(email, otp)
    return temp_token


async def _send_otp_email(to_email: str, otp: str):
    from app.utils.email_service import APP_ENV, send_email

    subject = "Your Synvex Login Verification Code"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Synvex Private Limited</h2>
        <p>Your verification code is:</p>
        <p style="font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #1B3A6B;">{otp}</p>
        <p>This code expires in {OTP_EXPIRY_MINUTES} minutes. If you did not request this, please ignore this email.</p>
    </div>
    """
    send_email(to_email, subject, html_body)


async def resend_otp(temp_token: str):
    from app.utils.auth import verify_token

    payload = verify_token(temp_token)
    if not payload or payload.get("purpose") != "2fa_pending":
        return None, "Invalid or expired session. Please log in again."

    db = get_db()
    challenge = await db.two_factor_challenges.find_one({"user_id": payload["user_id"]})
    if not challenge:
        return None, "No active verification session found"

    seconds_since_last = (datetime.utcnow() - challenge["last_sent_at"]).total_seconds()
    if seconds_since_last < OTP_RESEND_COOLDOWN_SECONDS:
        wait = int(OTP_RESEND_COOLDOWN_SECONDS - seconds_since_last)
        return None, f"Please wait {wait} seconds before requesting a new code"

    new_temp_token = await create_2fa_challenge(payload["user_id"], payload["email"], payload["role"])
    return new_temp_token, None


async def verify_otp(temp_token: str, otp: str):
    """
    Verifies the OTP against the stored hash. On success, returns the
    user payload needed to issue real access/refresh tokens.
    """
    from app.utils.auth import verify_token

    payload = verify_token(temp_token)
    if not payload or payload.get("purpose") != "2fa_pending":
        return None, "Invalid or expired session. Please log in again."

    db = get_db()
    challenge = await db.two_factor_challenges.find_one({"user_id": payload["user_id"]})
    if not challenge:
        return None, "No active verification session found. Please log in again."

    if datetime.utcnow() > challenge["expires_at"]:
        await db.two_factor_challenges.delete_one({"user_id": payload["user_id"]})
        return None, "Verification code expired. Please log in again to receive a new code."

    if challenge["attempts"] >= MAX_OTP_ATTEMPTS:
        await db.two_factor_challenges.delete_one({"user_id": payload["user_id"]})
        return None, "Too many incorrect attempts. Please log in again."

    if not verify_password(otp, challenge["otp_hash"]):
        await db.two_factor_challenges.update_one(
            {"user_id": payload["user_id"]},
            {"$inc": {"attempts": 1}}
        )
        remaining = MAX_OTP_ATTEMPTS - challenge["attempts"] - 1
        return None, f"Incorrect code. {max(remaining, 0)} attempts remaining."

    # Success — clean up the challenge
    await db.two_factor_challenges.delete_one({"user_id": payload["user_id"]})

    return {
        "user_id": payload["user_id"],
        "email": payload["email"],
        "role": payload["role"]
    }, None


def requires_2fa(role: str) -> bool:
    return role in ROLES_REQUIRING_2FA