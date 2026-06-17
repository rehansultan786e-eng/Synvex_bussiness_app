from app.database.connection import get_db
from app.models.asset import (
    AssetCreate, AssetUpdate, AssetAssignRequest,
    AssetReturnRequest, AssetTransferRequest,
    MaintenanceLogRequest
)
from app.services.audit_log import log_action
from datetime import datetime, date
from bson import ObjectId

# Configurable useful life for depreciation calculation (years)
DEFAULT_USEFUL_LIFE_YEARS = 5


def asset_helper(asset) -> dict:
    # Calculate straight-line depreciation (SRS AST-06)
    depreciated_value = None
    try:
        purchase_date = date.fromisoformat(str(asset["purchase_date"]))
        years_used = (date.today() - purchase_date).days / 365.25
        annual_depreciation = asset["purchase_cost"] / DEFAULT_USEFUL_LIFE_YEARS
        depreciated_value = max(
            0.0,
            round(asset["purchase_cost"] - (annual_depreciation * years_used), 2)
        )
    except Exception:
        pass

    return {
        "id": str(asset["_id"]),
        "asset_id": asset["asset_id"],
        "name": asset["name"],
        "category": asset["category"],
        "make": asset["make"],
        "model": asset["model"],
        "serial_number": asset["serial_number"],
        "purchase_date": str(asset["purchase_date"]),
        "purchase_cost": asset["purchase_cost"],
        "vendor": asset["vendor"],
        "warranty_expiry_date": str(asset["warranty_expiry_date"]) if asset.get("warranty_expiry_date") else None,
        "condition": asset["condition"],
        "status": asset["status"],
        "assigned_to": asset.get("assigned_to"),
        "assigned_to_name": asset.get("assigned_to_name"),
        "assignment_date": str(asset["assignment_date"]) if asset.get("assignment_date") else None,
        "expected_return_date": str(asset["expected_return_date"]) if asset.get("expected_return_date") else None,
        "acknowledged": asset.get("acknowledged", False),
        "has_photo": bool(asset.get("photo_base64")),
        "notes": asset.get("notes"),
        "depreciated_value": depreciated_value,
        "maintenance_history": asset.get("maintenance_history", []),
        "assignment_history": asset.get("assignment_history", []),
        "created_at": asset["created_at"],
        "updated_at": asset.get("updated_at")
    }


async def generate_asset_id():
    db = get_db()
    count = await db.assets.count_documents({})
    return f"AST-{count + 1:05d}"


async def create_asset(
    asset_data: AssetCreate, 
    created_by: str,
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    db = get_db()

    # Serial number must be unique
    existing = await db.assets.find_one({"serial_number": asset_data.serial_number})
    if existing:
        return None, "An asset with this serial number already exists"

    asset_id = await generate_asset_id()

    asset = {
        "asset_id": asset_id,
        "name": asset_data.name,
        "category": asset_data.category,
        "make": asset_data.make,
        "model": asset_data.model,
        "serial_number": asset_data.serial_number,
        "purchase_date": str(asset_data.purchase_date),
        "purchase_cost": asset_data.purchase_cost,
        "vendor": asset_data.vendor,
        "warranty_expiry_date": str(asset_data.warranty_expiry_date) if asset_data.warranty_expiry_date else None,
        "condition": asset_data.condition,
        "status": "Available",
        "assigned_to": None,
        "assigned_to_name": None,
        "assignment_date": None,
        "expected_return_date": None,
        "acknowledged": False,
        "photo_base64": asset_data.photo_base64.split(',')[-1] if asset_data.photo_base64 else None,
        "notes": asset_data.notes,
        "maintenance_history": [],
        "assignment_history": [],
        "created_by": created_by,
        "created_at": datetime.utcnow()
    }

    result = await db.assets.insert_one(asset)
    new_asset = await db.assets.find_one({"_id": result.inserted_id})
    payload = asset_helper(new_asset)

    # Log Asset Creation
    await log_action(
        user_id=created_by,
        user_name=actor_name,
        user_role=actor_role,
        action="CREATE",
        entity="asset",
        entity_id=asset_id,
        old_value=None,
        new_value=payload,
        description=f"Created corporate asset '{asset_data.name}' ({asset_id}) under category '{asset_data.category}'."
    )

    return payload, None


async def get_all_assets(
    status: str = None,
    category: str = None,
    assigned_to: str = None,
    search: str = None
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    if assigned_to:
        query["assigned_to"] = assigned_to
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"asset_id": {"$regex": search, "$options": "i"}},
            {"serial_number": {"$regex": search, "$options": "i"}},
            {"make": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
        ]

    assets = await db.assets.find(query).sort("created_at", -1).to_list(1000)
    return [asset_helper(a) for a in assets]


async def get_asset_by_id(asset_id: str):
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if asset:
        return asset_helper(asset)
    return None


async def update_asset(
    asset_id: str, 
    asset_data: AssetUpdate,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    db = get_db()
    old_asset = await db.assets.find_one({"asset_id": asset_id})
    if not old_asset:
        return None
    old_payload = asset_helper(old_asset)

    update_data = {k: v for k, v in asset_data.model_dump().items() if v is not None}
    if "warranty_expiry_date" in update_data:
        update_data["warranty_expiry_date"] = str(update_data["warranty_expiry_date"])
    update_data["updated_at"] = datetime.utcnow()
    
    await db.assets.update_one({"asset_id": asset_id}, {"$set": update_data})
    updated = await get_asset_by_id(asset_id)

    if updated:
        await log_action(
            user_id=actor_id,
            user_name=actor_name,
            user_role=actor_role,
            action="UPDATE",
            entity="asset",
            entity_id=asset_id,
            old_value=old_payload,
            new_value=updated,
            description=f"Updated core details for asset {asset_id}."
        )
    return updated


async def assign_asset(
    asset_id: str, 
    request: AssetAssignRequest,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    """
    AST-02: Assign asset to an employee.
    Asset must be Available. Sends notification to employee.
    """
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset:
        return None, "Asset not found"
    if asset["status"] != "Available":
        return None, f"Asset is currently {asset['status']} and cannot be assigned"

    old_payload = asset_helper(asset)

    employee = await db.employees.find_one({
        "employee_id": request.employee_id,
        "is_deleted": False
    })
    if not employee:
        return None, "Employee not found"

    assignment_record = {
        "employee_id": request.employee_id,
        "employee_name": employee["full_name"],
        "assignment_date": str(request.assignment_date),
        "expected_return_date": str(request.expected_return_date) if request.expected_return_date else None,
        "return_date": None,
        "condition_on_assignment": asset["condition"],
        "condition_on_return": None,
        "notes": request.notes,
        "acknowledged": False,
        "acknowledged_at": None
    }

    await db.assets.update_one(
        {"asset_id": asset_id},
        {
            "$set": {
                "status": "Assigned",
                "assigned_to": request.employee_id,
                "assigned_to_name": employee["full_name"],
                "assignment_date": str(request.assignment_date),
                "expected_return_date": str(request.expected_return_date) if request.expected_return_date else None,
                "acknowledged": False,
                "updated_at": datetime.utcnow()
            },
            "$push": {"assignment_history": assignment_record}
        }
    )

    # AST-02: Notify employee of asset assignment
    from app.services.notification import create_notification
    user = await db.users.find_one({"email": employee["email"]})
    notify_id = str(user["_id"]) if user else employee["employee_id"]
    await create_notification(
        user_id=notify_id,
        message=f"Asset {asset['name']} ({asset['asset_id']}) has been assigned to you. Please acknowledge receipt in the system.",
        notif_type="asset_assigned"
    )

    updated = await db.assets.find_one({"asset_id": asset_id})
    new_payload = asset_helper(updated)

    # Log Asset Assignment
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE_STATUS",
        entity="asset",
        entity_id=asset_id,
        old_value=old_payload,
        new_value=new_payload,
        description=f"Assigned asset {asset_id} to employee {employee['full_name']} ({request.employee_id})."
    )

    return new_payload, None


async def acknowledge_asset(asset_id: str, employee_id: str, actor_name: str = "Employee"):
    """
    AST-02: Employee digitally acknowledges receipt of assigned asset.
    """
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset:
        return None, "Asset not found"
    if asset.get("assigned_to") != employee_id:
        return None, "This asset is not assigned to you"

    old_payload = asset_helper(asset)

    # Update current assignment record in history
    history = asset.get("assignment_history", [])
    for record in reversed(history):
        if record["employee_id"] == employee_id and not record.get("return_date"):
            record["acknowledged"] = True
            record["acknowledged_at"] = datetime.utcnow().isoformat()
            break

    await db.assets.update_one(
        {"asset_id": asset_id},
        {"$set": {
            "acknowledged": True,
            "assignment_history": history,
            "updated_at": datetime.utcnow()
        }}
    )

    updated = await db.assets.find_one({"asset_id": asset_id})
    new_payload = asset_helper(updated)

    # Log Asset Acknowledgment
    await log_action(
        user_id=employee_id,
        user_name=actor_name,
        user_role="employee",
        action="UPDATE_STATUS",
        entity="asset",
        entity_id=asset_id,
        old_value=old_payload,
        new_value=new_payload,
        description=f"Employee {actor_name} digitally acknowledged receipt of asset {asset_id}."
    )

    return new_payload, None


async def return_asset(
    asset_id: str, 
    request: AssetReturnRequest,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    """
    AST-03: Mark asset as returned.
    AST-04: Flag if condition on return is worse than on assignment.
    """
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset:
        return None, "Asset not found"
    if asset["status"] != "Assigned":
        return None, "Asset is not currently assigned"

    old_payload = asset_helper(asset)

    condition_degraded = False
    condition_order = ["New", "Good", "Fair", "Damaged"]
    try:
        original_idx = condition_order.index(asset["condition"])
        return_idx = condition_order.index(request.condition_on_return)
        condition_degraded = return_idx > original_idx
    except ValueError:
        pass

    # Update last open assignment record in history
    history = asset.get("assignment_history", [])
    for record in reversed(history):
        if record["employee_id"] == asset["assigned_to"] and not record.get("return_date"):
            record["return_date"] = str(request.return_date)
            record["condition_on_return"] = request.condition_on_return
            record["condition_degraded"] = condition_degraded
            record["return_notes"] = request.notes
            break

    await db.assets.update_one(
        {"asset_id": asset_id},
        {
            "$set": {
                "status": "Available",
                "condition": request.condition_on_return,
                "assigned_to": None,
                "assigned_to_name": None,
                "assignment_date": None,
                "expected_return_date": None,
                "acknowledged": False,
                "assignment_history": history,
                "condition_degraded_on_return": condition_degraded,
                "updated_at": datetime.utcnow()
            }
        }
    )

    updated = await db.assets.find_one({"asset_id": asset_id})
    new_payload = asset_helper(updated)

    # Log Asset Return Action
    degraded_text = " with condition DEGRADATION flag" if condition_degraded else ""
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE_STATUS",
        entity="asset",
        entity_id=asset_id,
        old_value=old_payload,
        new_value=new_payload,
        description=f"Processed asset return for {asset_id}{degraded_text}. Status reset to Available."
    )

    return new_payload, ("CONDITION_DEGRADED" if condition_degraded else None)


async def transfer_asset(
    asset_id: str, 
    request: AssetTransferRequest,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    """
    AST-03: Transfer asset directly between employees.
    Closes current assignment and opens a new one.
    """
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset:
        return None, "Asset not found"
    if asset["status"] != "Assigned":
        return None, "Asset must be currently assigned to transfer"

    old_payload = asset_helper(asset)

    to_employee = await db.employees.find_one({
        "employee_id": request.to_employee_id,
        "is_deleted": False
    })
    if not to_employee:
        return None, "Target employee not found"

    # Close current assignment
    history = asset.get("assignment_history", [])
    for record in reversed(history):
        if record["employee_id"] == asset["assigned_to"] and not record.get("return_date"):
            record["return_date"] = str(request.transfer_date)
            record["condition_on_return"] = asset["condition"]
            record["return_notes"] = f"Transferred to {to_employee['full_name']}"
            break

    # New assignment record
    new_record = {
        "employee_id": request.to_employee_id,
        "employee_name": to_employee["full_name"],
        "assignment_date": str(request.transfer_date),
        "expected_return_date": None,
        "return_date": None,
        "condition_on_assignment": asset["condition"],
        "condition_on_return": None,
        "notes": request.notes,
        "acknowledged": False,
        "acknowledged_at": None
    }
    history.append(new_record)

    await db.assets.update_one(
        {"asset_id": asset_id},
        {
            "$set": {
                "assigned_to": request.to_employee_id,
                "assigned_to_name": to_employee["full_name"],
                "assignment_date": str(request.transfer_date),
                "expected_return_date": None,
                "acknowledged": False,
                "assignment_history": history,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Notify new employee
    from app.services.notification import create_notification
    user = await db.users.find_one({"email": to_employee["email"]})
    notify_id = str(user["_id"]) if user else to_employee["employee_id"]
    await create_notification(
        user_id=notify_id,
        message=f"Asset {asset['name']} ({asset_id}) has been transferred to you. Please acknowledge receipt.",
        notif_type="asset_assigned"
    )

    updated = await db.assets.find_one({"asset_id": asset_id})
    new_payload = asset_helper(updated)

    # Log Asset Transfer Action
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE_STATUS",
        entity="asset",
        entity_id=asset_id,
        old_value=old_payload,
        new_value=new_payload,
        description=f"Transferred asset {asset_id} ownership directly to employee {to_employee['full_name']}."
    )

    return new_payload, None


async def log_maintenance(
    asset_id: str, 
    maintenance_data: MaintenanceLogRequest,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    """AST-05: Log a maintenance record against an asset."""
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset:
        return None, "Asset not found"

    old_payload = asset_helper(asset)

    record = {
        "date": str(maintenance_data.date),
        "issue": maintenance_data.issue,
        "cost": maintenance_data.cost,
        "vendor": maintenance_data.vendor,
        "notes": maintenance_data.notes,
        "logged_at": datetime.utcnow().isoformat()
    }

    await db.assets.update_one(
        {"asset_id": asset_id},
        {
            "$push": {"maintenance_history": record},
            "$set": {
                "status": "Under Maintenance",
                "updated_at": datetime.utcnow()
            }
        }
    )

    updated = await db.assets.find_one({"asset_id": asset_id})
    new_payload = asset_helper(updated)

    # Log Maintenance Activity
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE_STATUS",
        entity="asset",
        entity_id=asset_id,
        old_value=old_payload,
        new_value=new_payload,
        description=f"Logged maintenance ticket for asset {asset_id}. Cost: {maintenance_data.cost}. Status shifted to 'Under Maintenance'."
    )

    return new_payload, None


async def complete_maintenance(
    asset_id: str,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    """Mark asset as Available after maintenance is complete."""
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset:
        return None, "Asset not found"

    old_payload = asset_helper(asset)

    await db.assets.update_one(
        {"asset_id": asset_id},
        {"$set": {"status": "Available", "updated_at": datetime.utcnow()}}
    )
    updated = await db.assets.find_one({"asset_id": asset_id})
    new_payload = asset_helper(updated)

    # Log Maintenance Resolution
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE_STATUS",
        entity="asset",
        entity_id=asset_id,
        old_value=old_payload,
        new_value=new_payload,
        description=f"Resolved maintenance for asset {asset_id}. Returned to Available status pool."
    )

    return new_payload, None


async def dispose_asset(
    asset_id: str,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "admin"
):
    """Mark asset as Disposed (end of life)."""
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset:
        return None, "Asset not found"
    if asset["status"] == "Assigned":
        return None, "Cannot dispose an asset that is currently assigned"

    old_payload = asset_helper(asset)

    await db.assets.update_one(
        {"asset_id": asset_id},
        {"$set": {"status": "Disposed", "updated_at": datetime.utcnow()}}
    )
    updated = await db.assets.find_one({"asset_id": asset_id})
    new_payload = asset_helper(updated)

    # Log Asset Disposal
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE_STATUS",
        entity="asset",
        entity_id=asset_id,
        old_value=old_payload,
        new_value=new_payload,
        description=f"Asset {asset_id} has been permanently decommissioned / disposed."
    )

    return new_payload, None


async def get_warranty_expiring_soon(days: int = 30):
    """
    AST-07: Assets with warranty expiring within N days.
    """
    from datetime import timedelta
    db = get_db()
    today = date.today()
    target = today + timedelta(days=days)
    assets = await db.assets.find({
        "warranty_expiry_date": {"$ne": None},
        "status": {"$ne": "Disposed"}
    }).to_list(1000)

    expiring = []
    for a in assets:
        if not a.get("warranty_expiry_date"):
            continue
        try:
            expiry = date.fromisoformat(str(a["warranty_expiry_date"]))
            if today <= expiry <= target:
                expiring.append(asset_helper(a))
        except Exception:
            continue
    return expiring


async def get_asset_report():
    """Total asset inventory with value and depreciation summary."""
    db = get_db()
    assets = await db.assets.find({}).to_list(1000)
    helpers = [asset_helper(a) for a in assets]

    total_purchase_value = sum(a["purchase_cost"] for a in assets)
    total_depreciated_value = sum(
        h["depreciated_value"] for h in helpers if h["depreciated_value"] is not None
    )

    by_status = {}
    by_category = {}
    for h in helpers:
        by_status[h["status"]] = by_status.get(h["status"], 0) + 1
        by_category[h["category"]] = by_category.get(h["category"], 0) + 1

    return {
        "total_assets": len(assets),
        "total_purchase_value": round(total_purchase_value, 2),
        "total_depreciated_value": round(total_depreciated_value, 2),
        "total_depreciation_to_date": round(total_purchase_value - total_depreciated_value, 2),
        "by_status": by_status,
        "by_category": by_category
    }