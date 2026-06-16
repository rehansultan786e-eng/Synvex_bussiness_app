# app/services/offboarding.py
#
# Offboarding service (SRS 6.7).
# HR initiates offboarding -> checklist tracked -> on completion,
# system access is revoked and experience letter can be generated.

from app.database.connection import get_db
from app.models.offboarding import OffboardingInitiate, OffboardingChecklistUpdate, ExperienceLetterDraft
from datetime import datetime
import io


def offboarding_helper(record) -> dict:
    return {
        "id": str(record["_id"]),
        "offboarding_id": record["offboarding_id"],
        "employee_id": record["employee_id"],
        "employee_name": record["employee_name"],
        "designation": record["designation"],
        "department": record["department"],
        "joining_date": record["joining_date"],
        "reason": record["reason"],
        "last_working_date": record["last_working_date"],
        "status": record["status"],
        "notes": record.get("notes"),
        "checklist": record["checklist"],
        "experience_letter_draft": record.get("experience_letter_draft"),
        "experience_letter_generated": record.get("experience_letter_generated", False),
        "initiated_by": record["initiated_by"],
        "created_at": record["created_at"],
        "completed_at": record.get("completed_at")
    }


async def generate_offboarding_id():
    db = get_db()
    count = await db.offboarding_records.count_documents({})
    return f"OFF-{count + 1:05d}"


DEFAULT_LETTER_TEMPLATE = """This is to certify that {full_name} ({employee_id}) worked at Synvex Private Limited as {designation} in the {department} department from {joining_date} to {last_working_date}.

During this period, {full_name} demonstrated professional conduct and contributed to the responsibilities assigned. We wish {full_name} success in future endeavors.

This letter is issued upon request for employment verification purposes."""


async def initiate_offboarding(data: OffboardingInitiate, initiated_by: str):
    """HR initiates offboarding when an employee resigns or is terminated (SRS 6.7)."""
    db = get_db()

    employee = await db.employees.find_one({"employee_id": data.employee_id, "is_deleted": False})
    if not employee:
        return None, "Employee not found"

    existing = await db.offboarding_records.find_one({
        "employee_id": data.employee_id,
        "status": "In Progress"
    })
    if existing:
        return None, "An offboarding process is already in progress for this employee"

    offboarding_id = await generate_offboarding_id()

    # Check if employee has any assets assigned (informs checklist starting state)
    assigned_assets = await db.assets.count_documents({"assigned_to": data.employee_id, "status": "Assigned"})

    letter_draft = DEFAULT_LETTER_TEMPLATE.format(
        full_name=employee["full_name"],
        employee_id=employee["employee_id"],
        designation=employee["designation"],
        department=employee["department"],
        joining_date=employee["joining_date"],
        last_working_date=str(data.last_working_date)
    )

    record = {
        "offboarding_id": offboarding_id,
        "employee_id": data.employee_id,
        "employee_name": employee["full_name"],
        "designation": employee["designation"],
        "department": employee["department"],
        "joining_date": employee["joining_date"],
        "reason": data.reason,
        "last_working_date": str(data.last_working_date),
        "status": "In Progress",
        "notes": data.notes,
        "checklist": {
            "assets_returned": assigned_assets == 0,
            "knowledge_transfer_completed": False,
            "final_payslip_generated": False,
            "exit_interview_completed": False,
            "access_revoked": False
        },
        "experience_letter_draft": letter_draft,
        "experience_letter_generated": False,
        "initiated_by": initiated_by,
        "created_at": datetime.utcnow(),
        "completed_at": None
    }

    result = await db.offboarding_records.insert_one(record)
    new_record = await db.offboarding_records.find_one({"_id": result.inserted_id})

    # Notify HR Manager and CEO that offboarding has started
    from app.services.notification import create_notification
    notify_users = await db.users.find({"role": {"$in": ["super_admin", "hr_manager"]}}).to_list(20)
    for u in notify_users:
        await create_notification(
            user_id=str(u["_id"]),
            message=f"Offboarding initiated for {employee['full_name']} ({data.employee_id}). Last working date: {data.last_working_date}.",
            notif_type="employee_onboarded"
        )

    return offboarding_helper(new_record), None


async def update_checklist(offboarding_id: str, checklist_update: OffboardingChecklistUpdate):
    """
    HR updates individual checklist items as offboarding progresses.
    When access_revoked is set True, the employee's account is deactivated immediately.
    """
    db = get_db()
    record = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    if not record:
        return None, "Offboarding record not found"

    if record["status"] != "In Progress":
        return None, f"Offboarding is already {record['status']}"

    current_checklist = record["checklist"]
    updates = {k: v for k, v in checklist_update.model_dump().items() if v is not None}
    current_checklist.update(updates)

    await db.offboarding_records.update_one(
        {"offboarding_id": offboarding_id},
        {"$set": {"checklist": current_checklist, "updated_at": datetime.utcnow()}}
    )

    # SRS 6.7: Employee's system access is revoked on the last working date
    if updates.get("access_revoked") is True:
        await db.employees.update_one(
            {"employee_id": record["employee_id"]},
            {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}}
        )

    # If all checklist items are complete, mark offboarding as Completed
    if all(current_checklist.values()):
        await db.offboarding_records.update_one(
            {"offboarding_id": offboarding_id},
            {"$set": {"status": "Completed", "completed_at": datetime.utcnow()}}
        )

    updated = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    return offboarding_helper(updated), None


async def update_experience_letter_draft(offboarding_id: str, draft: ExperienceLetterDraft):
    """HR manually edits the experience letter draft text before generating PDF."""
    db = get_db()
    record = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    if not record:
        return None, "Offboarding record not found"

    await db.offboarding_records.update_one(
        {"offboarding_id": offboarding_id},
        {"$set": {"experience_letter_draft": draft.letter_body, "updated_at": datetime.utcnow()}}
    )
    updated = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    return offboarding_helper(updated), None


def _build_experience_letter_pdf_bytes(employee_name: str, letter_body: str, offboarding_id: str) -> bytes:
    """Generates the experience letter as a professional PDF using reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1B3A6B"))

    elements = []
    elements.append(Paragraph("Synvex Private Limited", title_style))
    elements.append(Paragraph("Experience Letter", styles["Heading2"]))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}", styles["Normal"]))
    elements.append(Spacer(1, 1*cm))

    for paragraph in letter_body.split("\n\n"):
        elements.append(Paragraph(paragraph.replace("\n", "<br/>"), styles["Normal"]))
        elements.append(Spacer(1, 0.4*cm))

    elements.append(Spacer(1, 1.5*cm))
    elements.append(Paragraph("_____________________________", styles["Normal"]))
    elements.append(Paragraph("Authorised Signature, HR Department", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


async def generate_experience_letter(offboarding_id: str):
    """Generates the final experience letter PDF from the (HR-edited) draft text."""
    import base64

    db = get_db()
    record = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    if not record:
        return None, "Offboarding record not found"

    if not record.get("experience_letter_draft"):
        return None, "No experience letter draft found to generate from"

    pdf_bytes = _build_experience_letter_pdf_bytes(
        record["employee_name"], record["experience_letter_draft"], offboarding_id
    )
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    await db.offboarding_records.update_one(
        {"offboarding_id": offboarding_id},
        {"$set": {
            "experience_letter_pdf_base64": pdf_base64,
            "experience_letter_generated": True,
            "updated_at": datetime.utcnow()
        }}
    )
    updated = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    return offboarding_helper(updated), None


async def get_experience_letter_pdf_bytes(offboarding_id: str):
    import base64
    db = get_db()
    record = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    if not record or not record.get("experience_letter_pdf_base64"):
        return None
    return base64.b64decode(record["experience_letter_pdf_base64"])


async def get_offboarding_by_id(offboarding_id: str):
    db = get_db()
    record = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    if not record:
        return None
    return offboarding_helper(record)


async def get_all_offboarding_records(status: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    records = await db.offboarding_records.find(query).sort("created_at", -1).to_list(1000)
    return [offboarding_helper(r) for r in records]


async def cancel_offboarding(offboarding_id: str):
    db = get_db()
    record = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    if not record:
        return None, "Offboarding record not found"
    if record["status"] != "In Progress":
        return None, f"Cannot cancel - offboarding is already {record['status']}"

    await db.offboarding_records.update_one(
        {"offboarding_id": offboarding_id},
        {"$set": {"status": "Cancelled", "updated_at": datetime.utcnow()}}
    )
    updated = await db.offboarding_records.find_one({"offboarding_id": offboarding_id})
    return offboarding_helper(updated), None