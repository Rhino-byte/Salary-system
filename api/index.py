"""
Vercel serverless function entry point for FastAPI application.
"""
import sys
import os
from pathlib import Path
import importlib.util

# Add project root to Python path FIRST
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set working directory to project root for static files and templates
os.chdir(project_root)

# Ensure app/ package directory is importable before loading app.py
# This prevents the naming conflict between app.py and app/ package
app_package_path = project_root / "app"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import app.py as a module with a different name to avoid conflict
try:
    # Load app.py as a module named "main_app" to avoid conflict with "app" package
    app_file_path = project_root / "app.py"
    
    if not app_file_path.exists():
        raise FileNotFoundError(f"app.py not found at {app_file_path}")
    
    # Use importlib to load app.py as a module with a unique name
    spec = importlib.util.spec_from_file_location("main_app", app_file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create spec for {app_file_path}")
    
    main_app_module = importlib.util.module_from_spec(spec)
    
    # Add the module to sys.modules with a unique name to avoid conflicts
    sys.modules["main_app"] = main_app_module
    
    # Execute the module (this will import from app.config, app.models, etc.)
    spec.loader.exec_module(main_app_module)
    
    # Get the FastAPI app instance
    app = main_app_module.app
    
except Exception as e:
    # Better error handling for debugging
    import traceback
    print(f"Error importing app: {e}")
    print(f"Project root: {project_root}")
    print(f"App file path: {app_file_path}")
    print(f"App file exists: {app_file_path.exists() if 'app_file_path' in locals() else 'N/A'}")
    print(f"App package path: {app_package_path}")
    print(f"App package exists: {app_package_path.exists()}")
    print(f"Python path: {sys.path}")
    traceback.print_exc()
    raise

# Export the app for Vercel
handler = app
