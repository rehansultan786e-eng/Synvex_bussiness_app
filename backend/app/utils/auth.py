# app/utils/auth.py
#
# Authentication utilities: password hashing, JWT access/refresh tokens,
# and (NEW) invite tokens used for the "set your password" email flow.

from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# NEW: how long an invite link (set-password link) stays valid
INVITE_TOKEN_EXPIRE_HOURS = int(os.getenv("INVITE_TOKEN_EXPIRE_HOURS", 24))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===== EXISTING FUNCTIONS (unchanged) =====

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False
    except ValueError:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ===== NEW: Invite token functions =====
# Used for the "set your password" email link.
# The token encodes the user's id, email and role, with type="invite"
# and a fixed expiry (default 24 hours).

def create_invite_token(user_id: str, email: str, role: str) -> str:
    """
    Creates a short-lived JWT token to be embedded in the
    'Set Your Password' email link.
    """
    to_encode = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "type": "invite"
    }
    expire = datetime.utcnow() + timedelta(hours=INVITE_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_invite_token(token: str):
    """
    Verifies an invite token. Returns the decoded payload if valid
    and of type 'invite', otherwise returns None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "invite":
            return None
        return payload
    except JWTError:
        return None