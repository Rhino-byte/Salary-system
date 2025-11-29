"""
Migration script to add days_worked_this_month and total_days_worked columns to employee table.
Run this script to update existing database schema.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from app.models.schema import get_engine
from app.config.config import DATABASE_URL
from app.utils.attendance import update_employee_attendance
from app.models.schema import Employee

def migrate():
    """Add new columns and populate them with calculated values."""
    print("Connecting to database...")
    engine = get_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'employee' 
            AND column_name IN ('days_worked_this_month', 'total_days_worked')
        """))
        existing_columns = [row[0] for row in result]
        
        # Add days_worked_this_month if it doesn't exist
        if 'days_worked_this_month' not in existing_columns:
            print("Adding days_worked_this_month column...")
            conn.execute(text("""
                ALTER TABLE employee 
                ADD COLUMN days_worked_this_month INTEGER DEFAULT 0
            """))
            conn.commit()
            print("✓ Added days_worked_this_month column")
        else:
            print("✓ days_worked_this_month column already exists")
        
        # Add total_days_worked if it doesn't exist
        if 'total_days_worked' not in existing_columns:
            print("Adding total_days_worked column...")
            conn.execute(text("""
                ALTER TABLE employee 
                ADD COLUMN total_days_worked INTEGER DEFAULT 0
            """))
            conn.commit()
            print("✓ Added total_days_worked column")
        else:
            print("✓ total_days_worked column already exists")
    
    # Now populate the columns with calculated values
    print("\nCalculating and updating attendance for all employees...")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        employees = db.query(Employee).all()
        for employee in employees:
            print(f"  Updating {employee.first_name} {employee.last_name}...")
            update_employee_attendance(db, employee)
        print(f"\n✓ Updated attendance for {len(employees)} employees")
    except Exception as e:
        print(f"Error updating attendance: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
