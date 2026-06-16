# app/models/password_reset.py
#
# Password reset flow model (SRS 9.1): secure email link, expires in 15 minutes.

from pydantic import BaseModel, EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str