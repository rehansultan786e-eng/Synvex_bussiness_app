# app/routes/offboarding.py
#
# Offboarding routes (SRS 6.7).

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.offboarding import OffboardingInitiate, OffboardingChecklistUpdate, ExperienceLetterDraft
from app.services.offboarding import (
    initiate_offboarding, update_checklist, update_experience_letter_draft,
    generate_experience_letter, get_experience_letter_pdf_bytes,
    get_offboarding_by_id, get_all_offboarding_records, cancel_offboarding
)
from app.utils.dependencies import get_current_hr
from typing import Optional
import io

router = APIRouter(prefix="/api/offboarding", tags=["Offboarding"])


@router.post("/", status_code=201)
async def start_offboarding(
    data: OffboardingInitiate,
    current_user=Depends(get_current_hr)
):
    """HR Manager or CEO initiates offboarding for an employee."""
    record, error = await initiate_offboarding(data, initiated_by=current_user.get("user_id"))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Offboarding initiated successfully", "data": record}


@router.get("/")
async def list_offboarding_records(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_hr)
):
    records = await get_all_offboarding_records(status=status)
    return {"message": "Success", "data": records, "total": len(records)}


@router.get("/{offboarding_id}")
async def get_offboarding_record(offboarding_id: str, current_user=Depends(get_current_hr)):
    record = await get_offboarding_by_id(offboarding_id)
    if not record:
        raise HTTPException(status_code=404, detail="Offboarding record not found")
    return {"message": "Success", "data": record}


@router.put("/{offboarding_id}/checklist")
async def update_offboarding_checklist(
    offboarding_id: str,
    checklist_update: OffboardingChecklistUpdate,
    current_user=Depends(get_current_hr)
):
    """Updates checklist items; revokes employee access when access_revoked=True."""
    record, error = await update_checklist(offboarding_id, checklist_update)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Checklist updated successfully", "data": record}


@router.put("/{offboarding_id}/experience-letter/draft")
async def edit_experience_letter_draft(
    offboarding_id: str,
    draft: ExperienceLetterDraft,
    current_user=Depends(get_current_hr)
):
    """HR edits the experience letter draft text before generating the PDF."""
    record, error = await update_experience_letter_draft(offboarding_id, draft)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": "Experience letter draft updated", "data": record}


@router.post("/{offboarding_id}/experience-letter/generate")
async def generate_letter(offboarding_id: str, current_user=Depends(get_current_hr)):
    """Generates the final experience letter PDF from the (HR-edited) draft."""
    record, error = await generate_experience_letter(offboarding_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Experience letter generated successfully", "data": record}


@router.get("/{offboarding_id}/experience-letter/download")
async def download_experience_letter(offboarding_id: str, current_user=Depends(get_current_hr)):
    pdf_bytes = await get_experience_letter_pdf_bytes(offboarding_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="Experience letter not generated yet")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={offboarding_id}_experience_letter.pdf"}
    )


@router.put("/{offboarding_id}/cancel")
async def cancel_offboarding_route(offboarding_id: str, current_user=Depends(get_current_hr)):
    record, error = await cancel_offboarding(offboarding_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Offboarding cancelled successfully", "data": record}