"""
Service for sending notifications via Email and WhatsApp
Admins receive notifications about pending approvals
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from app.config.config import (
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM,
    ADMIN_NOTIFICATION_EMAIL, ENABLE_ADMIN_EMAIL_NOTIFICATIONS,
    WHATSAPP_ACCOUNT_SID, WHATSAPP_AUTH_TOKEN, WHATSAPP_FROM_NUMBER
)
from app.models.schema import Advance, Employee, OffDay
from sqlalchemy.orm import Session


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """
    Send email notification via Gmail
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            print("Email credentials not configured")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM or EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
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
    body = "\n".join(
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
    return send_email_notification(ADMIN_NOTIFICATION_EMAIL, subject, body)


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
    body = "\n".join(
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
    return send_email_notification(ADMIN_NOTIFICATION_EMAIL, subject, body)


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
            to=to_number
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
        "Details:"
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
    approved: bool
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

