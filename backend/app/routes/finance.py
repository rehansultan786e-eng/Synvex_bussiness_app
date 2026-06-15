from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.contract import (
    ContractCreate, ContractUpdate, MilestoneCreate,
    MilestoneUpdate, MilestonePaymentReceived
)
from app.models.invoice import InvoiceGenerateRequest
from app.services.contract import (
    create_contract, get_all_contracts, get_contract_by_id,
    update_contract, delete_contract, add_milestone,
    update_milestone, mark_milestone_received,
    get_overdue_milestones, get_upcoming_milestones
)
from app.services.invoice import (
    generate_invoice_for_milestone, get_invoice_pdf_bytes, send_invoice_email
)
from app.utils.dependencies import get_current_user, get_current_finance
from app.services.export import export_to_excel, export_to_pdf
from typing import Optional
import io

router = APIRouter(prefix="/api/finance", tags=["Finance"])


# ===== CONTRACTS (SRS 4.2) =====

@router.post("/contracts", status_code=201)
async def create_new_contract(
    contract_data: ContractCreate,
    current_user=Depends(get_current_finance)
):
    contract = await create_contract(contract_data, created_by=current_user.get("user_id"))
    return {"message": "Contract created successfully", "data": contract}


@router.get("/contracts")
async def list_contracts(
    client_name: Optional[str] = Query(None),
    current_user=Depends(get_current_finance)
):
    contracts = await get_all_contracts(client_name=client_name)
    return {"message": "Success", "data": contracts, "total": len(contracts)}


@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str, current_user=Depends(get_current_finance)):
    contract = await get_contract_by_id(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"message": "Success", "data": contract}


@router.put("/contracts/{contract_id}")
async def update_existing_contract(
    contract_id: str,
    contract_data: ContractUpdate,
    current_user=Depends(get_current_finance)
):
    contract = await update_contract(contract_id, contract_data)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"message": "Contract updated successfully", "data": contract}


@router.delete("/contracts/{contract_id}")
async def delete_existing_contract(contract_id: str, current_user=Depends(get_current_finance)):
    await delete_contract(contract_id)
    return {"message": "Contract deleted successfully"}


# ===== CONTRACT DOCUMENT UPLOAD (SRS 4.2.1) =====

@router.post("/contracts/{contract_id}/upload-document")
async def upload_contract_document(
    contract_id: str,
    file_base64: str,
    current_user=Depends(get_current_finance)
):
    """Stores the signed contract PDF as base64 in MongoDB (production-safe)."""
    from app.database.connection import get_db
    from datetime import datetime

    contract = await get_contract_by_id(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    db = get_db()
    await db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {
            "document_base64": file_base64.split(',')[-1],
            "document_url": f"/api/finance/contracts/{contract_id}/document",
            "updated_at": datetime.utcnow()
        }}
    )
    updated = await get_contract_by_id(contract_id)
    return {"message": "Contract document uploaded successfully", "data": updated}


@router.get("/contracts/{contract_id}/document")
async def download_contract_document(contract_id: str, current_user=Depends(get_current_finance)):
    from app.database.connection import get_db
    import base64

    db = get_db()
    contract = await db.contracts.find_one({"contract_id": contract_id, "is_deleted": False})
    if not contract or not contract.get("document_base64"):
        raise HTTPException(status_code=404, detail="Contract document not found")

    pdf_bytes = base64.b64decode(contract["document_base64"])
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={contract_id}.pdf"}
    )


# ===== MILESTONES (SRS 4.2.2) =====

@router.post("/contracts/{contract_id}/milestones")
async def add_contract_milestone(
    contract_id: str,
    milestone_data: MilestoneCreate,
    current_user=Depends(get_current_finance)
):
    contract, error = await add_milestone(contract_id, milestone_data)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": "Milestone added successfully", "data": contract}


@router.put("/contracts/{contract_id}/milestones/{milestone_id}")
async def update_contract_milestone(
    contract_id: str,
    milestone_id: str,
    milestone_data: MilestoneUpdate,
    current_user=Depends(get_current_finance)
):
    contract, error = await update_milestone(contract_id, milestone_id, milestone_data)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": "Milestone updated successfully", "data": contract}


@router.put("/contracts/{contract_id}/milestones/{milestone_id}/mark-received")
async def mark_milestone_paid(
    contract_id: str,
    milestone_id: str,
    payment_data: MilestonePaymentReceived,
    current_user=Depends(get_current_finance)
):
    contract, error = await mark_milestone_received(contract_id, milestone_id, payment_data)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": "Milestone marked as received", "data": contract}


@router.get("/milestones/overdue")
async def list_overdue_milestones(current_user=Depends(get_current_finance)):
    """FIN-03 / Outstanding Receivables report."""
    overdue = await get_overdue_milestones()
    return {"message": "Success", "data": overdue, "total": len(overdue)}


@router.get("/milestones/upcoming")
async def list_upcoming_milestones(
    days: int = Query(7),
    current_user=Depends(get_current_finance)
):
    """FIN-04: milestones due within N days — used for payment reminders."""
    upcoming = await get_upcoming_milestones(days)
    return {"message": "Success", "data": upcoming, "total": len(upcoming)}


@router.get("/milestones/overdue/export/excel")
async def export_overdue_milestones_excel(current_user=Depends(get_current_finance)):
    overdue = await get_overdue_milestones()
    columns = [
        ("contract_id", "Contract ID"),
        ("client_name", "Client"),
        ("project_name", "Project"),
        ("milestone_id", "Milestone ID"),
        ("description", "Description"),
        ("due_date", "Due Date"),
        ("amount", "Amount"),
        ("currency", "Currency"),
    ]
    return export_to_excel(overdue, columns, title="Outstanding Receivables")


# ===== INVOICES (SRS 4.2.3) =====

@router.post("/invoices/generate")
async def generate_invoice(
    request: InvoiceGenerateRequest,
    current_user=Depends(get_current_finance)
):
    invoice, error = await generate_invoice_for_milestone(request.contract_id, request.milestone_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": "Invoice generated successfully", "data": invoice}


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(invoice_id: str, current_user=Depends(get_current_finance)):
    pdf_bytes = await get_invoice_pdf_bytes(invoice_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={invoice_id}.pdf"}
    )


@router.post("/invoices/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    to_email: str,
    current_user=Depends(get_current_finance)
):
    success, error = await send_invoice_email(invoice_id, to_email)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Invoice sent successfully"}