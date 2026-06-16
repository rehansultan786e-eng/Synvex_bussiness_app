# app/models/two_factor.py
#
# Two-Factor Authentication model (SRS 9.1).
# Mandatory for super_admin (CEO) and finance_manager roles.
# Flow: email OTP, 6 digits, 5 minute expiry.

from pydantic import BaseModel, EmailStr


class TwoFactorVerifyRequest(BaseModel):
    temp_token: str   # short-lived token issued after password check, before OTP verify
    otp: str


class TwoFactorResendRequest(BaseModel):
    temp_token: str