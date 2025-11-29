"""
Vercel serverless function entry point for FastAPI application.
"""
import sys
import os
from pathlib import Path
import importlib.util

# Add project root to Python path FIRST
# In Vercel, api/index.py is at /var/task/api/index.py
# So project_root should be /var/task (parent of api/)
api_dir = Path(__file__).parent
project_root = api_dir.parent

# In Vercel, /var/task is the deployment root
# So if we're in /var/task/api/index.py, project_root is /var/task
# If project_root doesn't exist, try /var/task directly
if not project_root.exists() and Path("/var/task").exists():
    project_root = Path("/var/task")

# Debug: Print paths to understand the structure
print(f"API index.py location: {Path(__file__).resolve()}")
print(f"API directory: {api_dir.resolve()}")
print(f"Project root: {project_root.resolve()}")
print(f"Project root exists: {project_root.exists()}")
print(f"Current working directory: {os.getcwd()}")

# Add project root to Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set working directory to project root for static files and templates
if project_root.exists():
    os.chdir(project_root)
    print(f"Changed working directory to: {os.getcwd()}")
else:
    print(f"Warning: Project root {project_root} does not exist, keeping current directory")

# CRITICAL: Import the app package FIRST to register it in sys.modules
# This ensures that when main.py tries to import "from app.config.config",
# Python will find the app/ package, not app.py
try:
    # Import the app package to register it in sys.modules
    import app as app_package
    # Verify it's the package, not the file
    if not hasattr(app_package, '__path__'):
        # If app is a file module, we need to remove it and import the package
        if 'app' in sys.modules:
            del sys.modules['app']
        # Now import the package
        import app as app_package
    print(f"App package imported successfully: {app_package}")
except ImportError as e:
    print(f"Warning: Could not import app package: {e}")

# Now ensure app.py is NOT in sys.modules as 'app'
# Remove it if it exists
if 'app' in sys.modules:
    mod = sys.modules['app']
    # Check if it's a file module (app.py) not a package
    if not hasattr(mod, '__path__'):
        # It's app.py, remove it
        del sys.modules['app']
        # Re-import the package
        import app as app_package

# Now load main.py (renamed from app.py to avoid conflict) as a separate module
try:
    # Load main.py (app.py has been renamed to avoid conflict)
    # Try multiple possible locations
    possible_paths = [
        project_root / "main.py",
        Path("/var/task/main.py"),
        Path("main.py"),
    ]
    
    app_file_path = None
    for path in possible_paths:
        if path.exists():
            app_file_path = path
            print(f"Found main.py at: {app_file_path.resolve()}")
            break
    
    if app_file_path is None:
        # List what files actually exist
        print(f"Files in project root: {list(project_root.iterdir())}")
        print(f"Files in /var/task: {list(Path('/var/task').iterdir()) if Path('/var/task').exists() else 'N/A'}")
        raise FileNotFoundError(f"main.py not found. Searched: {possible_paths}")
    
    # Load the file as "main_app" module to avoid any conflicts
    spec = importlib.util.spec_from_file_location("main_app", app_file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create spec for {app_file_path}")
    
    main_app_module = importlib.util.module_from_spec(spec)
    
    # Register it with a unique name
    sys.modules["main_app"] = main_app_module
    
    # Execute the module - now when it does "from app.config.config",
    # Python will find the app/ package (already in sys.modules)
    spec.loader.exec_module(main_app_module)
    
    # Get the FastAPI app instance
    fastapi_app = main_app_module.app
    
    # Verify it's a FastAPI instance
    from fastapi import FastAPI
    if not isinstance(fastapi_app, FastAPI):
        raise TypeError(f"Expected FastAPI instance, got {type(fastapi_app)}")
    
    print(f"Successfully loaded FastAPI app: {type(fastapi_app)}")
    
except Exception as e:
    # Better error handling for debugging
    import traceback
    print(f"Error importing app: {e}")
    print(f"Project root: {project_root}")
    if 'app_file_path' in locals() and app_file_path is not None:
        print(f"App file path: {app_file_path}")
        print(f"App file exists: {app_file_path.exists()}")
    else:
        print(f"App file path: None (file not found)")
    print(f"App package in sys.modules: {'app' in sys.modules}")
    if 'app' in sys.modules:
        print(f"App module type: {type(sys.modules['app'])}")
        print(f"App module has __path__: {hasattr(sys.modules['app'], '__path__')}")
    print(f"Python path: {sys.path}")
    traceback.print_exc()
    raise

# Export the app for Vercel
# Vercel automatically detects FastAPI apps when exported as 'app'
# DO NOT export as 'handler' - that causes Vercel to check for BaseHTTPRequestHandler
# which fails because FastAPI apps are instances, not classes
app = fastapi_app
