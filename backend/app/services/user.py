# app/services/user.py
#
# Service functions for managing super_admin / admin / accountant users.
# Handles: inviting new users (admin/accountant), setting their password
# via invite link, fetching users, listing users, etc.
#
# These users are stored in the "users" MongoDB collection.
# Roles: super_admin, admin, accountant   (employee role is separate,
# stored in the "employees" collection as before)

from app.database.connection import get_db
from app.utils.auth import hash_password, create_invite_token, verify_invite_token
from app.utils.email_service import send_set_password_email
from datetime import datetime
from bson import ObjectId


def user_helper(user) -> dict:
    """Converts a MongoDB user document into a clean dict for API responses."""
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "is_active": user.get("is_active", False),
        "created_at": user["created_at"],
    }


async def get_user_by_email(email: str):
    db = get_db()
    return await db.users.find_one({"email": email})


async def get_user_by_id(user_id: str):
    db = get_db()
    try:
        return await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


async def get_all_users(role_filter: str = None):
    """
    Returns all users (super_admin/admin/accountant), optionally
    filtered by role. Used for listing in the admin dashboard.
    """
    db = get_db()
    query = {}
    if role_filter:
        query["role"] = role_filter

    users = await db.users.find(query).to_list(1000)
    return [user_helper(u) for u in users]


async def create_invited_user(full_name: str, email: str, role: str, created_by: str):
    """
    Creates a new user (admin or accountant) in 'pending invite' state:
    - is_active = False
    - password = "" (empty, will be set via invite link)
    Then sends a 'Set Your Password' email containing an invite token.

    Returns the created user dict, plus whether the email was sent successfully.
    """
    db = get_db()

    # Prevent duplicate accounts with the same email
    existing = await db.users.find_one({"email": email})
    if existing:
        return None, "Email already registered"

    new_user = {
        "full_name": full_name,
        "email": email,
        "role": role,             # "admin" or "accountant"
        "password": "",           # empty until user sets it via invite link
        "is_active": False,       # becomes True after password is set
        "created_by": created_by,  # user_id of the super_admin/admin who created this
        "created_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(new_user)
    user_id = str(result.inserted_id)

    # Generate invite token and send email (console-print in dev, real SMTP in prod)
    invite_token = create_invite_token(user_id=user_id, email=email, role=role)
    invite_sent = send_set_password_email(
        to_email=email,
        full_name=full_name,
        invite_token=invite_token,
        role=role
    )

    new_user["_id"] = result.inserted_id
    return user_helper(new_user), invite_sent


async def resend_invite(user_id: str):
    """
    Resends the 'Set Your Password' email for a user who hasn't
    activated their account yet.
    """
    db = get_db()
    user = await get_user_by_id(user_id)
    if not user:
        return False, "User not found"

    if user.get("is_active", False):
        return False, "User has already activated their account"

    invite_token = create_invite_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"]
    )
    invite_sent = send_set_password_email(
        to_email=user["email"],
        full_name=user["full_name"],
        invite_token=invite_token,
        role=user["role"]
    )
    return invite_sent, None


async def set_user_password_via_invite(token: str, new_password: str):
    """
    Verifies an invite token and sets the user's password,
    activating their account (is_active = True).
    """
    payload = verify_invite_token(token)
    if not payload:
        return False, "Invalid or expired invite link"

    db = get_db()
    user = await get_user_by_id(payload["user_id"])
    if not user:
        return False, "User not found"

    if user.get("is_active", False):
        return False, "This account has already been activated"

    hashed = hash_password(new_password)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": hashed, "is_active": True}}
    )
    return True, None