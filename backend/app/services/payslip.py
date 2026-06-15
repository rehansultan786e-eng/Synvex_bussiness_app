import io
import base64
from datetime import datetime
from app.database.connection import get_db


COMPANY_NAME = "Synvex Private Limited"
COMPANY_ADDRESS = "Office Address, City, Country"
MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def payslip_helper(payslip) -> dict:
    return {
        "id": str(payslip["_id"]),
        "payslip_id": payslip["payslip_id"],
        "employee_id": payslip["employee_id"],
        "employee_name": payslip["employee_name"],
        "month": payslip["month"],
        "year": payslip["year"],
        "pdf_url": payslip.get("pdf_url"),
        "generated_at": payslip["generated_at"],
        "sent_at": payslip.get("sent_at")
    }


def _build_payslip_pdf_bytes(record: dict, employee: dict, month: int, year: int, payslip_id: str) -> bytes:
    """Generates a professional payslip PDF (SRS 7.1 — Header, Employee Info, Earnings, Deductions, Net Pay, Footer)."""
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

    # Header
    elements.append(Paragraph(COMPANY_NAME, title_style))
    elements.append(Paragraph(COMPANY_ADDRESS, styles["Normal"]))
    elements.append(Paragraph(f"<b>Payslip for {MONTH_NAMES[month]} {year}</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.5*cm))

    # Employee Info
    elements.append(Paragraph(f"<b>Employee Name:</b> {employee['full_name']}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Employee ID:</b> {employee['employee_id']}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Designation:</b> {employee['designation']}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Department:</b> {employee['department']}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date of Joining:</b> {employee['joining_date']}", styles["Normal"]))
    elements.append(Spacer(1, 0.6*cm))

    # Earnings table
    earnings_data = [
        ["Earnings", "Amount"],
        ["Basic Salary", f"{record['basic_salary']:,.2f}"],
        ["Allowances (Total)", f"{record['allowances_total']:,.2f}"],
        ["Commission / Bonus", f"{record['commission_amount'] + record['bonus']:,.2f}"],
        ["Gross Pay", f"{record['gross_pay']:,.2f}"]
    ]
    earnings_table = Table(earnings_data, colWidths=[10*cm, 6*cm])
    earnings_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3A6B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(earnings_table)
    elements.append(Spacer(1, 0.5*cm))

    # Deductions table
    deductions_data = [
        ["Deductions", "Amount"],
        ["Total Deductions", f"{record['deductions_total']:,.2f}"],
    ]
    deductions_table = Table(deductions_data, colWidths=[10*cm, 6*cm])
    deductions_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3A6B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elements.append(deductions_table)
    elements.append(Spacer(1, 0.5*cm))

    # Net Pay
    net_data = [["Net Payable", f"{record['net_pay']:,.2f}"]]
    net_table = Table(net_data, colWidths=[10*cm, 6*cm])
    net_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2E5BA8")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 1.5*cm))

    # Footer
    elements.append(Paragraph("Bank account details for payment: [As on file with HR]", styles["Normal"]))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("_____________________________", styles["Normal"]))
    elements.append(Paragraph("Authorised Signature", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


async def generate_payslips_for_batch(batch_id: str):
    """
    SRS 7.2:
    3. System auto-generates individual PDF payslips for each employee.
    4. Payslip is available in the employee self-service portal immediately.
    5. System sends email notification to employee with payslip attached.
    """
    db = get_db()
    batch = await db.payroll_batches.find_one({"batch_id": batch_id})
    if not batch:
        return False, "Payroll batch not found"

    month, year = batch["month"], batch["year"]

    for record in batch["records"]:
        employee = await db.employees.find_one({"employee_id": record["employee_id"], "is_deleted": False})
        if not employee:
            continue

        payslip_id = f"PS-{year}-{month:02d}-{record['employee_id']}"

        existing = await db.payslips.find_one({"payslip_id": payslip_id})
        if existing:
            continue

        pdf_bytes = _build_payslip_pdf_bytes(record, employee, month, year, payslip_id)
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        payslip = {
            "payslip_id": payslip_id,
            "employee_id": record["employee_id"],
            "employee_name": record["employee_name"],
            "month": month,
            "year": year,
            "pdf_base64": pdf_base64,
            "pdf_url": f"/api/finance/payslips/{payslip_id}/download",
            "generated_at": datetime.utcnow(),
            "sent_at": None
        }
        await db.payslips.insert_one(payslip)

        # In-app notification (SRS 8.2 - "Payroll approved - payslip ready" -> All Employees)
        from app.services.notification import create_notification
        user = await db.users.find_one({"email": employee["email"]})
        notify_user_id = str(user["_id"]) if user else record["employee_id"]
        await create_notification(
            user_id=notify_user_id,
            message=f"Your payslip for {MONTH_NAMES[month]} {year} is now available.",
            notif_type="payroll_approved"
        )

        # Email payslip (dev mode = console log, production = real SMTP)
        await _send_payslip_email(employee["email"], employee["full_name"], pdf_bytes, payslip_id, month, year)

    return True, None


async def _send_payslip_email(to_email: str, employee_name: str, pdf_bytes: bytes, payslip_id: str, month: int, year: int):
    from app.utils.email_service import APP_ENV

    if APP_ENV != "production":
        print(f"\n[DEV MODE] Payslip {payslip_id} would be emailed to {to_email} ({employee_name}) - {MONTH_NAMES[month]} {year}\n")
        return

    from app.utils.email_service import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_FROM_NAME
    import smtplib
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    message = MIMEMultipart()
    message["Subject"] = f"Payslip - {MONTH_NAMES[month]} {year}"
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message.attach(MIMEText(f"Dear {employee_name},\n\nPlease find attached your payslip for {MONTH_NAMES[month]} {year}.\n\nRegards,\n{SMTP_FROM_NAME}", "plain"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=f"{payslip_id}.pdf")
    message.attach(attachment)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, to_email, message.as_string())
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send payslip to {to_email}: {e}")


async def get_payslip_pdf_bytes(payslip_id: str):
    db = get_db()
    payslip = await db.payslips.find_one({"payslip_id": payslip_id})
    if not payslip:
        return None
    return base64.b64decode(payslip["pdf_base64"])


async def get_employee_payslips(employee_id: str):
    db = get_db()
    payslips = await db.payslips.find({"employee_id": employee_id}).sort("year", -1).sort("month", -1).to_list(100)
    return [payslip_helper(p) for p in payslips]


async def get_all_payslips(month: int = None, year: int = None):
    db = get_db()
    query = {}
    if month:
        query["month"] = month
    if year:
        query["year"] = year
    payslips = await db.payslips.find(query).sort("generated_at", -1).to_list(1000)
    return [payslip_helper(p) for p in payslips]