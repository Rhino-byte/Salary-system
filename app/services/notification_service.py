"""
Service for sending notifications via Email and WhatsApp
Admins receive notifications about pending approvals
"""

import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

from app.config.config import (
    ADMIN_NOTIFICATION_EMAIL,
    APP_PUBLIC_URL,
    EMAIL_FROM,
    EMAIL_HOST,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_USER,
    ENABLE_ADMIN_EMAIL_NOTIFICATIONS,
    SMTP_USE_SSL,
    SMTP_USE_TLS,
    WHATSAPP_ACCOUNT_SID,
    WHATSAPP_AUTH_TOKEN,
    WHATSAPP_FROM_NUMBER,
)
from app.models.schema import Advance, Employee, OffDay
from sqlalchemy.orm import Session


def _admin_email_link_footer() -> tuple[str, str]:
    """
    Returns (plain_footer, html_footer_fragment) for app links in admin alert emails.
    """
    if not APP_PUBLIC_URL:
        plain = (
            "\n\nConfigure APP_PUBLIC_URL (or PUBLIC_APP_URL) on the server "
            "to include clickable links to this app in these emails."
        )
        frag = (
            '<p style="color:#64748b;font-size:12px;margin-top:16px">'
            "Configure APP_PUBLIC_URL on the server to include clickable app links."
            "</p>"
        )
        return plain, frag

    base = APP_PUBLIC_URL.rstrip("/")
    login_url = f"{base}/login"
    admin_url = f"{base}/admin-dashboard"

    plain = "\n".join(
        [
            "",
            "Open the app:",
            f"  • Login: {login_url}",
            f"  • Admin dashboard (Approvals): {admin_url}",
            "",
            "You may need to sign in before opening the admin dashboard.",
        ]
    )

    frag = f"""
<p style="margin-top:16px"><strong>Open the app</strong></p>
<ul style="margin-top:8px;padding-left:20px">
  <li style="margin-bottom:6px"><a href="{html.escape(login_url)}">Sign in</a></li>
  <li><a href="{html.escape(admin_url)}">Admin dashboard — Approvals</a></li>
</ul>
<p style="color:#64748b;font-size:12px;margin-top:12px">You may need to sign in before opening the admin dashboard.</p>
"""
    return plain, frag


def _wrap_notification_html(core_plain: str, footer_html: str) -> str:
    """Build a minimal HTML body: escaped request details + link footer."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8" /></head>
<body style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;font-size:14px;color:#0f172a;line-height:1.5">
<pre style="white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin:0 0 8px 0;font-family:inherit">{html.escape(core_plain)}</pre>
{footer_html}
</body>
</html>"""


def send_email_notification(
    to_email: str,
    subject: str,
    body: str,
    body_html: str | None = None,
) -> bool:
    """
    Send email via SMTP (STARTTLS on port 587 by default, or SMTP_SSL on 465 when configured).

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain-text body
        body_html: Optional HTML body (multipart/alternative when set)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            print("Email credentials not configured")
            return False

        msg: MIMEMultipart
        if body_html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, "plain", "utf-8"))

        msg["From"] = EMAIL_FROM or EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        else:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            if SMTP_USE_TLS:
                server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def notify_admin_new_advance(session: Session, advance_id: int) -> bool:
    """
    Email the configured admin when a new advance request is created (pending).
    """
    if not ENABLE_ADMIN_EMAIL_NOTIFICATIONS or not ADMIN_NOTIFICATION_EMAIL:
        return False
    advance = session.query(Advance).filter(Advance.id == advance_id).first()
    if not advance:
        return False
    employee = session.query(Employee).filter(Employee.id == advance.employee_id).first()
    name = f"{employee.first_name} {employee.last_name}" if employee else f"ID {advance.employee_id}"
    st = advance.status.value if hasattr(advance.status, "value") else str(advance.status)
    reason = (advance.reason or "").strip() or "(none)"
    subject = f"[Salary] New advance request #{advance_id} ({st})"

    core_plain = "\n".join(
        [
            "A new salary advance request was submitted.",
            "",
            f"Request ID: {advance_id}",
            f"Employee: {name} (employee_id={advance.employee_id})",
            f"Amount: {advance.amount_for_advance:.2f}",
            f"Status: {st}",
            f"Reason: {reason}",
            f"Created: {advance.created_at}",
            "",
            "Review in the admin dashboard to approve or deny.",
        ]
    )

    footer_plain, footer_html = _admin_email_link_footer()
    body_plain = core_plain + footer_plain
    body_html = _wrap_notification_html(core_plain, footer_html)

    return send_email_notification(
        ADMIN_NOTIFICATION_EMAIL,
        subject,
        body_plain,
        body_html,
    )


def notify_admin_new_off_day(session: Session, off_day_id: int) -> bool:
    """
    Email the configured admin when a new off-day request is created (pending).
    """
    if not ENABLE_ADMIN_EMAIL_NOTIFICATIONS or not ADMIN_NOTIFICATION_EMAIL:
        return False
    off = session.query(OffDay).filter(OffDay.id == off_day_id).first()
    if not off:
        return False
    employee = session.query(Employee).filter(Employee.id == off.employee_id).first()
    name = f"{employee.first_name} {employee.last_name}" if employee else f"ID {off.employee_id}"
    st = off.status.value if hasattr(off.status, "value") else str(off.status)
    reason = (off.reason or "").strip() or "(none)"
    subject = f"[Salary] New off-day request #{off_day_id} ({st})"

    core_plain = "\n".join(
        [
            "A new off-day request was submitted.",
            "",
            f"Request ID: {off_day_id}",
            f"Employee: {name} (employee_id={off.employee_id})",
            f"Start date: {off.date}",
            f"Day count: {off.day_count}",
            f"Type: {off.off_type}",
            f"Status: {st}",
            f"Reason: {reason}",
            f"Created: {off.created_at}",
            "",
            "Review in the admin dashboard to approve or deny.",
        ]
    )

    footer_plain, footer_html = _admin_email_link_footer()
    body_plain = core_plain + footer_plain
    body_html = _wrap_notification_html(core_plain, footer_html)

    return send_email_notification(
        ADMIN_NOTIFICATION_EMAIL,
        subject,
        body_plain,
        body_html,
    )


def send_whatsapp_notification(to_number: str, message: str) -> bool:
    """
    Send WhatsApp notification via Twilio

    Args:
        to_number: Recipient WhatsApp number (format: whatsapp:+1234567890)
        message: Message to send

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        if not WHATSAPP_ACCOUNT_SID or not WHATSAPP_AUTH_TOKEN:
            print("WhatsApp credentials not configured")
            return False

        client = Client(WHATSAPP_ACCOUNT_SID, WHATSAPP_AUTH_TOKEN)

        message = client.messages.create(
            body=message,
            from_=WHATSAPP_FROM_NUMBER,
            to=to_number,
        )

        print(f"WhatsApp message sent successfully to {to_number}")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp message: {str(e)}")
        return False


def send_pending_advances_summary(session: Session, admin_id: int) -> bool:
    """
    Send summary of pending advances to admin via email and WhatsApp

    Args:
        session: Database session
        admin_id: ID of admin to notify

    Returns:
        True if notifications sent successfully
    """
    # Get admin details
    admin = session.query(Employee).filter(Employee.id == admin_id).first()
    if not admin:
        return False

    # Get pending advances
    from app.services.advance_service import get_pending_advances

    pending_advances = get_pending_advances(session)

    if not pending_advances:
        return True  # No pending advances, nothing to notify

    # Build summary message
    summary_lines = [
        "Salary Management System - Pending Advance Requests",
        "=" * 50,
        f"Total Pending: {len(pending_advances)}",
        "",
        "Details:",
    ]

    total_amount = 0
    for advance in pending_advances:
        employee = advance.employee
        summary_lines.append(
            f"- ID: {advance.id} | "
            f"Employee: {employee.first_name} {employee.last_name} | "
            f"Amount: ${advance.amount_for_advance:.2f} | "
            f"Date: {advance.created_at.strftime('%Y-%m-%d')}"
        )
        if advance.reason:
            summary_lines.append(f"  Reason: {advance.reason}")
        total_amount += advance.amount_for_advance

    summary_lines.append("")
    summary_lines.append(f"Total Amount: ${total_amount:.2f}")
    summary_lines.append("")
    summary_lines.append("Please review and approve/deny these requests.")

    summary_text = "\n".join(summary_lines)

    # Send email (if admin has email configured)
    # Note: You may want to add email field to Employee table
    # For now, we'll use a placeholder or skip email

    # Send WhatsApp (if admin has phone number)
    if admin.phone_no:
        whatsapp_number = f"whatsapp:{admin.phone_no}"
        send_whatsapp_notification(whatsapp_number, summary_text)

    return True


def send_advance_decision_notification(
    session: Session,
    advance_id: int,
    approved: bool,
) -> bool:
    """
    Notify employee about advance decision

    Args:
        session: Database session
        advance_id: ID of advance
        approved: Whether advance was approved

    Returns:
        True if notification sent successfully
    """
    advance = session.query(Advance).filter(Advance.id == advance_id).first()
    if not advance or not advance.employee:
        return False

    employee = advance.employee
    status = "APPROVED" if approved else "DENIED"

    message = (
        f"Your advance request (ID: {advance.id}, Amount: ${advance.amount_for_advance:.2f}) "
        f"has been {status}."
    )

    if advance.approval_notes:
        message += f"\nNotes: {advance.approval_notes}"

    # Send WhatsApp notification
    if employee.phone_no:
        whatsapp_number = f"whatsapp:{employee.phone_no}"
        send_whatsapp_notification(whatsapp_number, message)

    return True
