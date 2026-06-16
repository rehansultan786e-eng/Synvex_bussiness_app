# seed_super_admin.py
#
# One-time setup script to create the initial super_admin (CEO) account.
# Run manually from the backend directory:
#     python seed_super_admin.py
#
# Safe to run multiple times — it will skip creation if a super_admin
# already exists, or if the given email is already registered.

import asyncio
import os
import sys
import getpass
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import connect_db, disconnect_db, get_db
from app.utils.auth import hash_password
from app.utils.password_policy import validate_password_strength


async def seed_super_admin():
    await connect_db()
    db = get_db()

    existing_super_admin = await db.users.find_one({"role": "super_admin"})
    if existing_super_admin:
        print(f"\nA super_admin account already exists: {existing_super_admin['email']}")
        print("Seeding skipped. Delete the existing super_admin record manually if you need to re-seed.\n")
        await disconnect_db()
        return

    print("\n===== Synvex — Super Admin (CEO) Account Setup =====\n")

    full_name = input("Full name: ").strip()
    while not full_name:
        full_name = input("Full name cannot be empty. Full name: ").strip()

    email = input("Email: ").strip()
    while not email or "@" not in email:
        email = input("Please enter a valid email: ").strip()

    existing_email = await db.users.find_one({"email": email})
    if existing_email:
        print(f"\nAn account with email '{email}' already exists. Aborting.\n")
        await disconnect_db()
        return

    while True:
        password = getpass.getpass("Password (min 8 chars, upper/lower/number/special): ")
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            print(f"  -> {error_msg}\n")
            continue
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("  -> Passwords do not match. Try again.\n")
            continue
        break

    super_admin = {
        "full_name": full_name,
        "email": email,
        "role": "super_admin",
        "password": hash_password(password),
        "is_active": True,
        "created_by": "seed_script",
        "created_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(super_admin)
    print(f"\nSuper Admin account created successfully.")
    print(f"  ID:    {result.inserted_id}")
    print(f"  Email: {email}")
    print(f"  Role:  super_admin\n")
    print("You can now log in with this account. Note: super_admin and finance_manager")
    print("roles require 2FA (email OTP) at login.\n")

    await disconnect_db()


if __name__ == "__main__":
    asyncio.run(seed_super_admin())