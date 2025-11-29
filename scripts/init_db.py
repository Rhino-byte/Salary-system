"""
Initialize the database with schema
Run this script to create all tables in your Neon database
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` package can be imported when running from scripts/
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.schema import create_tables, get_engine
from app.config.config import DATABASE_URL

if __name__ == "__main__":
    print("Connecting to database...")
    engine = get_engine(DATABASE_URL)
    
    print("Creating tables...")
    create_tables(engine)
    
    print("Database initialization complete!")

