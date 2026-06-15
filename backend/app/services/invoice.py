import io
from datetime import datetime
from app.database.connection import get_db
from app.services.contract import get_contract_by_id


COMPANY_NAME = "Synvex Private Limited"
COMPANY_ADDRESS = "Office Address, City, Country"
COMPANY_BANK_DETAILS = "Bank Name: [Bank] | Account Title: Synvex Private Limited | Account No: [XXXXXXXX] | IBAN: [XXXXXXXX]"


def invoice_helper(invoice) -> dict:
    return {
        "id": str(invoice["_id"]),
        "invoice_id": invoice["invoice_id"],
        "contract_id": invoice["contract_id"],
        "milestone_id": invoice["milestone_id"],
        "client_name": invoice["client_name"],
        "project_name": invoice["project_name"],
        "description": invoice["description"],
        "amount": invoice["amount"],
        "currency": invoice["currency"],
        "pdf_url": invoice.get("pdf_url"),
        "sent_at": invoice.get("sent_at"),
        "created_at": invoice["created_at"]
    }


async def generate_invoice_number():
    db = get_db()
    count = await db.invoices.count_documents({})
    return f"INV-{count + 1:05d}"


def _build_invoice_pdf_bytes(invoice_id: str, client_name: str, project_name: str,
                              description: str, amount: float, currency: str) -> bytes:
    """Generates a professional invoice PDF using reportlab. Returns raw PDF bytes."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1B3A6B"))
    elements = []

    elements.append(Paragraph(COMPANY_NAME, title_style))
    elements.append(Paragraph(COMPANY_ADDRESS, styles["Normal"]))
    elements.append(Spacer(1, 0.8*cm))

    elements.append(Paragraph(f"<b>Invoice Number:</b> {invoice_id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}", styles["Normal"]))
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph(f"<b>Bill To:</b> {client_name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Project:</b> {project_name}", styles["Normal"]))
    elements.append(Spacer(1, 0.8*cm))

    table_data = [
        ["Description", "Amount"],
        [description, f"{amount:,.2f} {currency}"]
    ]
    table = Table(table_data, colWidths=[12*cm, 5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3A6B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 12),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1.5*cm))

    elements.append(Paragraph("<b>Bank Details for Payment:</b>", styles["Normal"]))
    elements.append(Paragraph(COMPANY_BANK_DETAILS, styles["Normal"]))
    elements.append(Spacer(1, 1.5*cm))

    elements.append(Paragraph("_____________________________", styles["Normal"]))
    elements.append(Paragraph("Authorised Signature", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


async def generate_invoice_for_milestone(contract_id: str, milestone_id: str):
    """FIN-02: Auto-generate a professional invoice PDF for a milestone."""
    db = get_db()
    contract = await get_contract_by_id(contract_id)
    if not contract:
        return None, "Contract not found"

    milestone = None
    for m in contract["milestones"]:
        if m["milestone_id"] == milestone_id:
            milestone = m
            break

    if not milestone:
        return None, "Milestone not found"

    existing = await db.invoices.find_one({"milestone_id": milestone_id})
    if existing:
        return invoice_helper(existing), None

    invoice_id = await generate_invoice_number()

    pdf_bytes = _build_invoice_pdf_bytes(
        invoice_id=invoice_id,
        client_name=contract["client_name"],
        project_name=contract["project_name"],
        description=f"Milestone {milestone['milestone_number']}: {milestone['description']}",
        amount=milestone["amount"],
        currency=contract["currency"]
    )

    # Store PDF as base64 in DB (consistent with face_images approach - production-safe, no filesystem dependency)
    import base64
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    invoice = {
        "invoice_id": invoice_id,
        "contract_id": contract_id,
        "milestone_id": milestone_id,
        "client_name": contract["client_name"],
        "project_name": contract["project_name"],
        "description": f"Milestone {milestone['milestone_number']}: {milestone['description']}",
        "amount": milestone["amount"],
        "currency": contract["currency"],
        "pdf_base64": pdf_base64,
        "pdf_url": None,
        "sent_at": None,
        "created_at": datetime.utcnow()
    }
    result = await db.invoices.insert_one(invoice)
    new_invoice = await db.invoices.find_one({"_id": result.inserted_id})
    return invoice_helper(new_invoice), None


async def get_invoice_pdf_bytes(invoice_id: str):
    """Returns raw PDF bytes for download, decoded from stored base64."""
    import base64
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id})
    if not invoice:
        return None
    return base64.b64decode(invoice["pdf_base64"])


async def send_invoice_email(invoice_id: str, to_email: str):
    """FIN: Send invoice directly via email from the system."""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id})
    if not invoice:
        return False, "Invoice not found"

    import base64
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from app.utils.email_service import APP_ENV, send_email

    pdf_bytes = base64.b64decode(invoice["pdf_base64"])

    if APP_ENV != "production":
        print(f"\n[DEV MODE] Invoice {invoice_id} would be emailed to {to_email} with PDF attachment ({len(pdf_bytes)} bytes)\n")
    else:
        from app.utils.email_service import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_FROM_NAME
        import smtplib

        message = MIMEMultipart()
        message["Subject"] = f"Invoice {invoice_id} - {invoice['project_name']}"
        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message.attach(MIMEText(f"Please find attached invoice {invoice_id} for {invoice['project_name']}.", "plain"))

        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename=f"{invoice_id}.pdf")
        message.attach(attachment)

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM_EMAIL, to_email, message.as_string())
        except Exception as e:
            return False, str(e)

    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"sent_at": datetime.utcnow()}}
    )
    return True, None