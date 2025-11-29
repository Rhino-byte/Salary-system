"""
Vercel serverless function entry point for FastAPI application.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set working directory to project root for static files and templates
os.chdir(project_root)

# Import the FastAPI app
try:
    from app import app
except Exception as e:
    # Better error handling for debugging
    import traceback
    print(f"Error importing app: {e}")
    traceback.print_exc()
    raise

# Export the app for Vercel
handler = app
