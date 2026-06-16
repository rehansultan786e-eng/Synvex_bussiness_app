# app/utils/password_policy.py
#
# Password policy validator (SRS 9.1):
# Minimum 8 characters, must include uppercase, lowercase, number, special character.

import re


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message). error_message is empty if valid."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]", password):
        return False, "Password must contain at least one special character"
    return True, ""