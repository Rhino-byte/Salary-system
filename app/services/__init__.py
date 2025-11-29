"""
Services Package
"""

from .advance_service import (
    request_advance,
    approve_advance,
    get_pending_advances,
    get_employee_advances
)

from .bill_service import (
    add_bill,
    update_bill,
    get_employee_bills,
    get_staff_bills,
    get_all_bills,
    get_recorded_bills
)

from .auth_service import (
    check_permission,
    can_request_advance,
    can_add_bills,
    can_approve_advances,
    can_view_all
)

from .notification_service import (
    send_email_notification,
    send_whatsapp_notification,
    send_pending_advances_summary,
    send_advance_decision_notification
)

__all__ = [
    # Advance service
    'request_advance',
    'approve_advance',
    'get_pending_advances',
    'get_employee_advances',
    # Bill service
    'add_bill',
    'update_bill',
    'get_employee_bills',
    'get_staff_bills',
    'get_all_bills',
    'get_recorded_bills',
    # Auth service
    'check_permission',
    'can_request_advance',
    'can_add_bills',
    'can_approve_advances',
    'can_view_all',
    # Notification service
    'send_email_notification',
    'send_whatsapp_notification',
    'send_pending_advances_summary',
    'send_advance_decision_notification'
]

