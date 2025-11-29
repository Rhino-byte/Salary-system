"""
Example usage of the Salary Management System
This demonstrates how to use the various services
"""

from app.models.schema import get_engine, get_session, Employee, Role
from app.config.config import DATABASE_URL
from app.services.advance_service import request_advance, approve_advance, get_pending_advances
from app.services.bill_service import add_bill, update_bill, get_employee_bills, get_staff_bills
from app.services.notification_service import send_pending_advances_summary
from app.services.auth_service import can_request_advance, can_add_bills, can_approve_advances


def example_workflow():
    """Example workflow demonstrating the system"""
    
    # Initialize database connection
    engine = get_engine(DATABASE_URL)
    session = get_session(engine)
    
    try:
        # Example 1: Create employees
        print("Creating employees...")
        
        staff1 = Employee(
            first_name="John",
            last_name="Doe",
            role=Role.STAFF,
            salary=5000.00,
            phone_no="+1234567890"
        )
        
        manager1 = Employee(
            first_name="Jane",
            last_name="Smith",
            role=Role.MANAGER,
            salary=8000.00,
            phone_no="+1234567891"
        )
        
        admin1 = Employee(
            first_name="Bob",
            last_name="Johnson",
            role=Role.ADMIN,
            salary=10000.00,
            phone_no="+1234567892"
        )
        
        session.add_all([staff1, manager1, admin1])
        session.commit()
        session.refresh(staff1)
        session.refresh(manager1)
        session.refresh(admin1)
        
        print(f"Created staff: {staff1.id}, manager: {manager1.id}, admin: {admin1.id}")
        
        # Example 2: Staff requests advance
        print("\nStaff requesting advance...")
        if can_request_advance(session, staff1.id):
            advance1 = request_advance(
                session=session,
                employee_id=staff1.id,
                amount=500.00,
                reason="Emergency medical expenses"
            )
            print(f"Advance requested: PIN {advance1.pin}, Amount: ${advance1.amount}")
        else:
            print("Permission denied")
        
        # Example 2b: Manager requests advance (NEW FEATURE)
        print("\nManager requesting advance...")
        if can_request_advance(session, manager1.id):
            advance2 = request_advance(
                session=session,
                employee_id=manager1.id,
                amount=800.00,
                reason="Business trip expenses"
            )
            print(f"Advance requested: PIN {advance2.pin}, Amount: ${advance2.amount}")
        else:
            print("Permission denied")
        
        # Example 3: Manager adds bill for staff
        print("\nManager adding bill for staff...")
        if can_add_bills(session, manager1.id):
            bill1 = add_bill(
                session=session,
                recorded_by_id=manager1.id,
                employee_id=staff1.id,
                amount=150.00,
                reason="Office supplies"
            )
            print(f"Bill added: PIN {bill1.pin}, Amount: ${bill1.amount}, Recorded by: {bill1.manager_name}")
        else:
            print("Permission denied")
        
        # Example 3b: Admin adds bill for manager (NEW FEATURE)
        print("\nAdmin adding bill for manager...")
        if can_add_bills(session, admin1.id):
            bill2 = add_bill(
                session=session,
                recorded_by_id=admin1.id,
                employee_id=manager1.id,
                amount=300.00,
                reason="Conference registration"
            )
            print(f"Bill added: PIN {bill2.pin}, Amount: ${bill2.amount}, Recorded by: {bill2.manager_name}")
        else:
            print("Permission denied")
        
        # Example 4: Admin views pending advances
        print("\nAdmin viewing pending advances...")
        if can_approve_advances(session, admin1.id):
            pending = get_pending_advances(session)
            print(f"Found {len(pending)} pending advance(s)")
            for adv in pending:
                print(f"  - PIN: {adv.pin}, Employee: {adv.employee.first_name}, Amount: ${adv.amount}")
            
            # Send notification to admin
            send_pending_advances_summary(session, admin1.id)
            
            # Admin approves advance
            if pending:
                approved_advance = approve_advance(
                    session=session,
                    advance_id=pending[0].id,
                    admin_id=admin1.id,
                    approved=True,
                    notes="Approved for emergency expenses"
                )
                print(f"Advance {approved_advance.pin} approved")
        else:
            print("Permission denied: Only admins can approve advances")
        
        # Example 5: View employee bills
        print("\nViewing bills for staff member...")
        bills = get_employee_bills(session, staff1.id)
        print(f"Found {len(bills)} bill(s) for staff member")
        for bill in bills:
            print(f"  - PIN: {bill.pin}, Amount: ${bill.amount}, Date: {bill.date}, Recorded by: {bill.manager_name}")
        
        # Example 5b: View manager bills (NEW FEATURE)
        print("\nViewing bills for manager...")
        manager_bills = get_employee_bills(session, manager1.id)
        print(f"Found {len(manager_bills)} bill(s) for manager")
        for bill in manager_bills:
            print(f"  - PIN: {bill.pin}, Amount: ${bill.amount}, Date: {bill.date}, Recorded by: {bill.manager_name}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    print("Salary Management System - Example Usage")
    print("=" * 50)
    example_workflow()

