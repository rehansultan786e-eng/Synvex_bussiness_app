# app/routes/audit_log.py
#
# Audit Log routes (SRS 9.4 / FIN-10).
# Read-only. Only Super Admin (CEO) can view audit logs.

from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.audit_log import get_all_audit_logs, get_entity_history
from app.services.export import export_to_excel
from app.utils.dependencies import get_current_super_admin
from typing import Optional

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("/")
async def list_audit_logs(
    entity: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_super_admin)
):
    """Super Admin only — paginated, filterable audit trail."""
    result = await get_all_audit_logs(
        entity=entity, action=action, user_id=user_id,
        page=page, page_size=page_size
    )
    return {"message": "Success", "data": result}


@router.get("/entity/{entity}/{entity_id}")
async def entity_audit_history(
    entity: str,
    entity_id: str,
    current_user=Depends(get_current_super_admin)
):
    """Full history of changes for one specific record."""
    history = await get_entity_history(entity, entity_id)
    return {"message": "Success", "data": history, "total": len(history)}


@router.get("/export/excel")
async def export_audit_logs_excel(
    entity: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    current_user=Depends(get_current_super_admin)
):
    result = await get_all_audit_logs(entity=entity, action=action, page=1, page_size=10000)
    columns = [
        ("log_id", "Log ID"),
        ("timestamp", "Timestamp"),
        ("user_name", "User"),
        ("user_role", "Role"),
        ("action", "Action"),
        ("entity", "Entity"),
        ("entity_id", "Entity ID"),
        ("description", "Description"),
    ]
    return export_to_excel(result["logs"], columns, title="Audit Log Report")