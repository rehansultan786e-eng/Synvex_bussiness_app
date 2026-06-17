# app/services/leave_balance.py
#
# Leave balance management (SRS 6.4.1 / 6.4.2).
# Tracks per-employee, per-year leave balances across leave types.
# Balances are initialized when an employee is created and deducted
# automatically when a leave request is approved.

from app.database.connection import get_db
from app.models.leave import DEFAULT_LEAVE_QUOTAS
from datetime import datetime, date


def _empty_balances_for_year() -> dict:
    """Builds the starting balance structure using default annual quotas."""
    balances = {}
    for leave_type, quota in DEFAULT_LEAVE_QUOTAS.items():
        balances[leave_type] = {
            "quota": quota,       # None means unlimited (e.g. Unpaid)
            "used": 0,
            "remaining": quota    # None stays None (unlimited)
        }
    return balances


async def initialize_leave_balance(employee_id: str, year: int = None):
    """
    Called when a new employee is created (or when a new year starts).
    Creates a fresh balance record if one doesn't already exist for that year.
    """
    db = get_db()
    target_year = year or date.today().year

    existing = await db.leave_balances.find_one({"employee_id": employee_id, "year": target_year})
    if existing:
        return existing

    record = {
        "employee_id": employee_id,
        "year": target_year,
        "balances": _empty_balances_for_year(),
        "created_at": datetime.utcnow()
    }
    await db.leave_balances.insert_one(record)
    return record


async def get_leave_balance(employee_id: str, year: int = None):
    """Returns the employee's leave balance for the given year, creating it if missing."""
    target_year = year or date.today().year
    db = get_db()
    record = await db.leave_balances.find_one({"employee_id": employee_id, "year": target_year})
    if not record:
        record = await initialize_leave_balance(employee_id, target_year)

    return {
        "employee_id": record["employee_id"],
        "year": record["year"],
        "balances": record["balances"]
    }


async def has_sufficient_balance(employee_id: str, leave_type: str, days_requested: int, year: int = None) -> tuple[bool, str]:
    """
    Checks whether the employee has enough remaining balance for the
    requested leave type. Unpaid leave always passes (no quota limit).
    """
    if leave_type == "Unpaid":
        return True, ""

    balance = await get_leave_balance(employee_id, year)
    type_balance = balance["balances"].get(leave_type)

    if not type_balance or type_balance["quota"] is None:
        return True, ""

    if type_balance["remaining"] < days_requested:
        return False, f"Insufficient {leave_type} leave balance. Remaining: {type_balance['remaining']} day(s), requested: {days_requested} day(s)."

    return True, ""


async def deduct_leave_balance(employee_id: str, leave_type: str, days: int, year: int = None):
    """
    SRS 6.4.2: Leave balance is deducted automatically on approval.
    Unpaid leave does not deduct from any quota (it has none).
    """
    if leave_type == "Unpaid":
        return True

    target_year = year or date.today().year
    db = get_db()

    balance = await get_leave_balance(employee_id, target_year)
    balances = balance["balances"]

    type_balance = balances.get(leave_type)
    if not type_balance or type_balance["quota"] is None:
        return True  # unlimited type, nothing to deduct

    type_balance["used"] += days
    type_balance["remaining"] = max(0, type_balance["quota"] - type_balance["used"])

    await db.leave_balances.update_one(
        {"employee_id": employee_id, "year": target_year},
        {"$set": {"balances": balances, "updated_at": datetime.utcnow()}}
    )
    return True


async def restore_leave_balance(employee_id: str, leave_type: str, days: int, year: int = None):
    """
    Used if an approved leave is later cancelled/reversed — restores the
    deducted days back to the employee's balance.
    """
    if leave_type == "Unpaid":
        return True

    target_year = year or date.today().year
    db = get_db()

    balance = await get_leave_balance(employee_id, target_year)
    balances = balance["balances"]

    type_balance = balances.get(leave_type)
    if not type_balance or type_balance["quota"] is None:
        return True

    type_balance["used"] = max(0, type_balance["used"] - days)
    type_balance["remaining"] = min(type_balance["quota"], type_balance["quota"] - type_balance["used"])

    await db.leave_balances.update_one(
        {"employee_id": employee_id, "year": target_year},
        {"$set": {"balances": balances, "updated_at": datetime.utcnow()}}
    )
    return True