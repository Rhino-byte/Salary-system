"""
Utility functions for the Salary Management System
"""

from app.models.schema import get_engine, get_session, Employee, Role
from app.config.config import DATABASE_URL


def create_sample_data():
    """Create sample employees for testing"""
    engine = get_engine(DATABASE_URL)
    session = get_session(engine)
    
    try:
        # Check if employees already exist
        existing = session.query(Employee).count()
        if existing > 0:
            print("Sample data already exists. Skipping creation.")
            return
        
        # Create sample staff
        staff1 = Employee(
            first_name="John",
            last_name="Doe",
            role=Role.STAFF,
            salary=5000.00,
            phone_no="+1234567890"
        )
        
        staff2 = Employee(
            first_name="Alice",
            last_name="Williams",
            role=Role.STAFF,
            salary=4500.00,
            phone_no="+1234567893"
        )
        
        # Create sample manager
        manager1 = Employee(
            first_name="Jane",
            last_name="Smith",
            role=Role.MANAGER,
            salary=8000.00,
            phone_no="+1234567891"
        )
        
        # Create sample admin
        admin1 = Employee(
            first_name="Bob",
            last_name="Johnson",
            role=Role.ADMIN,
            salary=10000.00,
            phone_no="+1234567892"
        )
        
        session.add_all([staff1, staff2, manager1, admin1])
        session.commit()
        
        print("Sample data created successfully!")
        print(f"Staff: {staff1.id} ({staff1.first_name} {staff1.last_name})")
        print(f"Staff: {staff2.id} ({staff2.first_name} {staff2.last_name})")
        print(f"Manager: {manager1.id} ({manager1.first_name} {manager1.last_name})")
        print(f"Admin: {admin1.id} ({admin1.first_name} {admin1.last_name})")
        
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    create_sample_data()

