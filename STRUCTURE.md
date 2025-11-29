# Project Structure Documentation

This document describes the organized folder structure of the Salary Management System.

## Directory Overview

### `/app`
Main application package containing all Python application code.

#### `/app/models`
Database models and schema definitions.
- `schema.py`: SQLAlchemy models (Employee, BillAdvance, Role, AdvanceStatus)

#### `/app/services`
Business logic and service layer.
- `advance_service.py`: Handle advance requests
- `auth_service.py`: Role-based permission checks
- `bill_service.py`: Bill management operations
- `notification_service.py`: Email and WhatsApp notifications

#### `/app/config`
Configuration and environment settings.
- `config.py`: Database URLs, email settings, WhatsApp credentials

### `/templates`
HTML templates for the web interface.
- `login.html`: Login page with video background
- `admin_dashboard.html`: Admin dashboard page

### `/static`
Static assets (images, videos, CSS, JavaScript).

#### `/static/images`
Image assets.
- `logo.jpg`: Application logo (used as favicon and login logo)

#### `/static/videos`
Video assets.
- `login_abstract.mp4`: Background video for login page

### `/scripts`
Utility scripts and examples.
- `init_db.py`: Initialize database tables
- `example_usage.py`: Example workflow demonstrations
- `utils.py`: Utility functions (sample data creation)

### Root Level Files
- `requirements.txt`: Python package dependencies
- `README.md`: Main project documentation
- `.gitignore`: Git ignore rules
- `STRUCTURE.md`: This file

## Import Paths

### Before (Old Structure)
```python
from schema import Employee, BillAdvance
from config import DATABASE_URL
from advance_service import request_advance
```

### After (New Structure)
```python
from app.models.schema import Employee, BillAdvance
from app.config.config import DATABASE_URL
from app.services.advance_service import request_advance
```

Or using package imports:
```python
from app.models import Employee, BillAdvance
from app.config import DATABASE_URL
from app.services import request_advance
```

## File Paths in Templates

### Static Assets
- Logo: `../static/images/logo.jpg`
- Video: `../static/videos/login_abstract.mp4`

These paths are relative to the template files in `/templates`.

## Benefits of This Structure

1. **Organization**: Clear separation of concerns
2. **Scalability**: Easy to add new features
3. **Maintainability**: Related files grouped together
4. **Best Practices**: Follows Python package conventions
5. **Clarity**: Easy to find specific functionality

