from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.asset import (
    AssetCreate, AssetUpdate, AssetAssignRequest,
    AssetReturnRequest, AssetTransferRequest,
    MaintenanceLogRequest, AssetAcknowledgement
)
from app.services.asset import (
    create_asset, get_all_assets, get_asset_by_id,
    update_asset, assign_asset, acknowledge_asset,
    return_asset, transfer_asset, log_maintenance,
    complete_maintenance, dispose_asset,
    get_warranty_expiring_soon, get_asset_report
)
from app.services.export import export_to_excel, export_to_pdf
from app.utils.dependencies import get_current_user, get_current_hr
from typing import Optional
import io

router = APIRouter(prefix="/api/assets", tags=["Assets"])


# ===== ASSET REGISTRY (AST-01) =====
@router.post("/", status_code=201)
async def create_new_asset(
    asset_data: AssetCreate,
    current_user=Depends(get_current_hr)
):
    asset, error = await create_asset(asset_data, created_by=current_user.get("user_id"))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Asset registered successfully", "data": asset}


@router.get("/")
async def list_assets(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
):
    """
    HR Manager / Finance / CEO: see all assets.
    Employee: sees only their assigned assets (enforced via assigned_to filter).
    """
    role = current_user.get("role")
    if role == "employee":
        assigned_to = current_user.get("employee_id") or current_user.get("user_id")

    assets = await get_all_assets(
        status=status, category=category,
        assigned_to=assigned_to, search=search
    )
    return {"message": "Success", "data": assets, "total": len(assets)}


@router.get("/report")
async def asset_inventory_report(current_user=Depends(get_current_hr)):
    """Full asset inventory summary with values and depreciation (AST-06)."""
    report = await get_asset_report()
    return {"message": "Success", "data": report}


@router.get("/warranty-expiring")
async def warranty_expiring(
    days: int = Query(30),
    current_user=Depends(get_current_hr)
):
    """AST-07: Assets with warranty expiring within N days."""
    assets = await get_warranty_expiring_soon(days=days)
    return {"message": "Success", "data": assets, "total": len(assets)}


@router.get("/{asset_id}")
async def get_asset(asset_id: str, current_user=Depends(get_current_user)):
    asset = await get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Employees can only view their own assigned assets
    role = current_user.get("role")
    if role == "employee":
        emp_id = current_user.get("employee_id") or current_user.get("user_id")
        if asset["assigned_to"] != emp_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return {"message": "Success", "data": asset}


@router.put("/{asset_id}")
async def update_existing_asset(
    asset_id: str,
    asset_data: AssetUpdate,
    current_user=Depends(get_current_hr)
):
    asset = await get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    updated = await update_asset(asset_id, asset_data)
    return {"message": "Asset updated successfully", "data": updated}


# ===== ASSET PHOTO =====
@router.get("/{asset_id}/photo")
async def get_asset_photo(asset_id: str, current_user=Depends(get_current_user)):
    from app.database.connection import get_db
    import base64
    db = get_db()
    asset = await db.assets.find_one({"asset_id": asset_id})
    if not asset or not asset.get("photo_base64"):
        raise HTTPException(status_code=404, detail="Photo not found")
    photo_bytes = base64.b64decode(asset["photo_base64"])
    return StreamingResponse(io.BytesIO(photo_bytes), media_type="image/jpeg")


# ===== ASSIGNMENT (AST-02) =====
@router.post("/{asset_id}/assign")
async def assign_asset_to_employee(
    asset_id: str,
    request: AssetAssignRequest,
    current_user=Depends(get_current_hr)
):
    """Assign asset to an employee — sends notification for acknowledgement."""
    asset, error = await assign_asset(asset_id, request)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Asset assigned successfully", "data": asset}


@router.post("/{asset_id}/acknowledge")
async def acknowledge_asset_receipt(
    asset_id: str,
    current_user=Depends(get_current_user)
):
    """
    AST-02: Employee digitally acknowledges receipt of assigned asset.
    """
    employee_id = current_user.get("employee_id") or current_user.get("user_id")
    asset, error = await acknowledge_asset(asset_id, employee_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Asset acknowledged successfully", "data": asset}


# ===== RETURN (AST-03, AST-04) =====
@router.post("/{asset_id}/return")
async def return_asset_from_employee(
    asset_id: str,
    request: AssetReturnRequest,
    current_user=Depends(get_current_hr)
):
    """
    AST-03: Mark asset returned.
    AST-04: Flags condition degradation automatically.
    """
    asset, flag = await return_asset(asset_id, request)
    if asset is None:
        raise HTTPException(status_code=400, detail=flag)

    message = "Asset returned successfully"
    if flag == "CONDITION_DEGRADED":
        message = "Asset returned — condition degraded from assignment. Please review."

    return {"message": message, "condition_degraded": flag == "CONDITION_DEGRADED", "data": asset}


# ===== TRANSFER (AST-03) =====
@router.post("/{asset_id}/transfer")
async def transfer_asset_between_employees(
    asset_id: str,
    request: AssetTransferRequest,
    current_user=Depends(get_current_hr)
):
    """AST-03: Transfer asset directly between employees."""
    asset, error = await transfer_asset(asset_id, request)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Asset transferred successfully", "data": asset}


# ===== MAINTENANCE (AST-05) =====
@router.post("/{asset_id}/maintenance")
async def log_asset_maintenance(
    asset_id: str,
    maintenance_data: MaintenanceLogRequest,
    current_user=Depends(get_current_hr)
):
    """AST-05: Log a maintenance record and set asset status to Under Maintenance."""
    asset, error = await log_maintenance(asset_id, maintenance_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Maintenance logged successfully", "data": asset}


@router.put("/{asset_id}/maintenance/complete")
async def complete_asset_maintenance(
    asset_id: str,
    current_user=Depends(get_current_hr)
):
    """Mark maintenance complete and set asset back to Available."""
    asset, error = await complete_maintenance(asset_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Maintenance completed — asset marked Available", "data": asset}


# ===== DISPOSE =====
@router.put("/{asset_id}/dispose")
async def dispose_existing_asset(
    asset_id: str,
    current_user=Depends(get_current_hr)
):
    """Mark asset as Disposed (end of life)."""
    asset, error = await dispose_asset(asset_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Asset marked as disposed", "data": asset}


# ===== EXPORTS =====
@router.get("/export/excel")
async def export_assets_excel(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user=Depends(get_current_hr)
):
    assets = await get_all_assets(status=status, category=category)
    columns = [
        ("asset_id", "Asset ID"),
        ("name", "Name"),
        ("category", "Category"),
        ("make", "Make"),
        ("model", "Model"),
        ("serial_number", "Serial No"),
        ("purchase_date", "Purchase Date"),
        ("purchase_cost", "Purchase Cost"),
        ("condition", "Condition"),
        ("status", "Status"),
        ("assigned_to_name", "Assigned To"),
        ("warranty_expiry_date", "Warranty Expiry"),
        ("depreciated_value", "Depreciated Value"),
    ]
    return export_to_excel(assets, columns, title="Asset Inventory")


@router.get("/export/pdf")
async def export_assets_pdf(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user=Depends(get_current_hr)
):
    assets = await get_all_assets(status=status, category=category)
    columns = [
        ("asset_id", "Asset ID"),
        ("name", "Name"),
        ("category", "Category"),
        ("status", "Status"),
        ("assigned_to_name", "Assigned To"),
        ("purchase_cost", "Cost"),
        ("depreciated_value", "Current Value"),
    ]
    return export_to_pdf(assets, columns, title="Asset Inventory")