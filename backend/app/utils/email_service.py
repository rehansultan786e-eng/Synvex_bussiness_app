# app/utils/email_service.py
#
# Email service for sending invite links / password-set links.
# - In DEVELOPMENT: emails are printed to console/logs (no real email sent).
# - In PRODUCTION: emails are sent via real SMTP using credentials from .env
#
# Switch is controlled by ENV variable: APP_ENV=development / production

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# ===== CONFIGURATION (read from .env) =====
APP_ENV = os.getenv("APP_ENV", "development")  # "development" or "production"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@synvex.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Synvex Attendance System")

# Frontend base URL, used to build the "set password" link
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Sends an email. Returns True if sent (or simulated) successfully.

    DEVELOPMENT mode: prints the email content to console, returns True.
    PRODUCTION mode: sends a real email via SMTP, returns True/False based on success.
    """

    # ===== DEVELOPMENT MODE: just print to console =====
    if APP_ENV != "production":
        print("\n========== [DEV MODE] EMAIL SIMULATION ==========")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("Body (HTML):")
        print(html_body)
        print("===================================================\n")
        return True

    # ===== PRODUCTION MODE: send real email via SMTP =====
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = to_email

        message.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, to_email, message.as_string())

        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        return False


def send_set_password_email(to_email: str, full_name: str, invite_token: str, role: str) -> bool:
    """
    Sends the 'Set your password' invite email to a newly created
    admin / accountant / employee user.

    The link points to the frontend page that will collect the new password
    and call the backend's set-password endpoint.
    """

    # Build the link that the user will click to set their password
    set_password_link = f"{FRONTEND_BASE_URL}/set-password?token={invite_token}"

    subject = "Set up your account - Synvex Attendance System"

    # Simple HTML email body
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">
        <h2>Welcome to Synvex Attendance System</h2>
        <p>Hi {full_name},</p>
        <p>An account has been created for you with the role: <b>{role}</b>.</p>
        <p>Please click the button below to set your password and activate your account:</p>
        <p>
            <a href="{set_password_link}"
               style="background:#2563eb;color:#fff;padding:10px 20px;
                      text-decoration:none;border-radius:6px;display:inline-block;">
                Set Your Password
            </a>
        </p>
        <p>If the button doesn't work, copy this link into your browser:</p>
        <p>{set_password_link}</p>
        <p>If you did not expect this email, please ignore it.</p>
    </div>
    """

    return send_email(to_email, subject, html_body)