# Vercel Deployment Guide

This guide will help you deploy the Salary Management System to Vercel.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. Your Neon database connection string
3. Git repository (GitHub, GitLab, or Bitbucket)

## Setup Steps

### 1. Environment Variables

In your Vercel project settings, add the following environment variables:

- `DATABASE_URL`: Your Neon PostgreSQL connection string
  - Format: `postgresql://user:password@host/database?sslmode=require`
  - Get this from your Neon dashboard

Optional (for notifications):
- `EMAIL_HOST`: SMTP host (default: smtp.gmail.com)
- `EMAIL_PORT`: SMTP port (default: 587)
- `EMAIL_USER`: Your email address
- `EMAIL_PASSWORD`: Your email password
- `EMAIL_FROM`: Sender email address
- `WHATSAPP_ACCOUNT_SID`: Twilio account SID
- `WHATSAPP_AUTH_TOKEN`: Twilio auth token
- `WHATSAPP_FROM_NUMBER`: Twilio WhatsApp number

### 2. Deploy to Vercel

#### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# For production deployment
vercel --prod
```

#### Option B: Using GitHub Integration

1. Push your code to GitHub
2. Go to https://vercel.com/new
3. Import your GitHub repository
4. Vercel will automatically detect the configuration
5. Add environment variables in the project settings
6. Deploy

### 3. Project Structure

The deployment uses the following structure:

```
.
├── api/
│   └── index.py          # Vercel serverless function entry point
├── app/
│   ├── config/
│   ├── models/
│   ├── services/
│   └── utils/
├── static/               # Static files (images, videos)
├── templates/            # HTML templates
├── app.py               # Main FastAPI application
├── vercel.json          # Vercel configuration
└── requirements.txt     # Python dependencies
```

### 4. Important Notes

- **Database Connection**: Make sure your `DATABASE_URL` is set correctly in Vercel environment variables
- **Static Files**: Static files are served from the `/static` directory
- **Templates**: HTML templates are served from the `/templates` directory
- **Cold Starts**: First request may be slower due to serverless cold starts

### 5. Troubleshooting

#### Error: FUNCTION_INVOCATION_FAILED

1. Check that `DATABASE_URL` is set in Vercel environment variables
2. Verify the database connection string is correct
3. Check Vercel function logs for detailed error messages
4. Ensure all dependencies are in `requirements.txt`

#### Error: Module not found

1. Verify all imports are correct
2. Check that `PYTHONPATH` is set correctly (handled by vercel.json)
3. Ensure all Python packages are in `requirements.txt`

#### Static files not loading

1. Verify static files are in the `static/` directory
2. Check that paths in HTML templates use `/static/...` format
3. Ensure `vercel.json` routes are configured correctly

### 6. Testing the Deployment

After deployment, test these endpoints:

- `https://your-project.vercel.app/` - Should show login page
- `https://your-project.vercel.app/health` - Health check endpoint
- `https://your-project.vercel.app/api/employees` - API endpoint

### 7. Database Migration

After deployment, you may need to run the migration script to add the attendance columns:

```bash
# This should be run locally or via a script, not on Vercel
python scripts/migrate_add_attendance_columns.py
```

Or manually add the columns to your database:
```sql
ALTER TABLE employee ADD COLUMN IF NOT EXISTS days_worked_this_month INTEGER DEFAULT 0;
ALTER TABLE employee ADD COLUMN IF NOT EXISTS total_days_worked INTEGER DEFAULT 0;
```

## Support

If you encounter issues:
1. Check Vercel function logs in the dashboard
2. Verify all environment variables are set
3. Test database connectivity
4. Check that all dependencies are installed
