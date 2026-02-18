# 🚀 Deployment Guide: Railway + Supabase

## Complete Step-by-Step Guide for Deploying AI-Based Section Placement System

---

## 📋 Prerequisites

Before starting, make sure you have:

- [ ] GitHub account (for code hosting)
- [ ] Email address (for Railway and Supabase accounts)
- [ ] Your project code pushed to GitHub

---

## 🗂️ PHASE 1: Push Code to GitHub

### Step 1.1: Create GitHub Repository

1. **Go to GitHub**: https://github.com
2. **Click** the green **"New"** button (or go to https://github.com/new)
3. **Fill in details**:
   - Repository name: `ai-section-placement` (or your preferred name)
   - Description: "AI-Based Section Placement System for ZNHS West"
   - Visibility: **Private** (recommended) or Public
4. **Click** "Create repository"

### Step 1.2: Push Your Code

Open terminal in your project folder and run:

```powershell
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - ready for deployment"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ai-section-placement.git

# Push to GitHub
git push -u origin main
```

**Note**: If your default branch is `master` instead of `main`:

```powershell
git push -u origin master
```

---

## 🗄️ PHASE 2: Set Up Supabase Database

### Step 2.1: Create Supabase Account

1. **Go to**: https://supabase.com
2. **Click** "Start your project" or "Sign Up"
3. **Sign up** with GitHub (recommended) or email
4. **Verify** your email if required

### Step 2.2: Create New Project

1. **Click** "New Project"
2. **Select** your organization (or create one)
3. **Fill in project details**:
   - **Name**: `znhs-section-placement` (or your choice)
   - **Database Password**: Create a STRONG password
     - ⚠️ **SAVE THIS PASSWORD** - you'll need it later!
     - Example: `MyStr0ng!Passw0rd#2026`
   - **Region**: Choose **Southeast Asia (Singapore)** for Philippines
   - **Pricing Plan**: Free tier
4. **Click** "Create new project"
5. **Wait** 2-3 minutes for project to be ready

### Step 2.3: Get Database Connection String

1. In your Supabase project, go to **Settings** (gear icon in sidebar)
2. Click **Database** in the left menu
3. Scroll down to **Connection string**
4. Select **URI** tab
5. Choose **Transaction pooler** mode (recommended for web apps)
6. **Copy** the connection string

It looks like this:

```
postgres://postgres.abcdefghijklmnop:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

7. **Replace** `[YOUR-PASSWORD]` with your actual database password
8. **Save** this complete connection string somewhere safe - you'll need it for Railway!

**Example final connection string:**

```
postgres://postgres.abcdefghijklmnop:MyStr0ng!Passw0rd#2026@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

---

## 🚂 PHASE 3: Set Up Railway

### Step 3.1: Create Railway Account

1. **Go to**: https://railway.app
2. **Click** "Login" → "Login with GitHub"
3. **Authorize** Railway to access your GitHub
4. **Verify** your account (may require email verification)

### Step 3.2: Create New Project

1. **Click** "New Project"
2. **Select** "Deploy from GitHub repo"
3. **Find** your repository in the list
4. **Click** on your repo name (e.g., `ai-section-placement`)
5. Railway will start deploying immediately (it will fail - that's expected!)

### Step 3.3: Configure Environment Variables

**This is the most important step!**

1. **Click** on your service (the purple box)
2. Go to **Variables** tab
3. **Click** "New Variable" and add these one by one:

| Variable Name            | Value                                          | Description             |
| ------------------------ | ---------------------------------------------- | ----------------------- |
| `SECRET_KEY`             | Generate new one (see below)                   | Django security key     |
| `DATABASE_URL`           | Your Supabase connection string                | Database connection     |
| `DEBUG`                  | `False`                                        | Production mode         |
| `DJANGO_SETTINGS_MODULE` | `section_placement_system.settings_production` | Use production settings |
| `GEMINI_API_KEY`         | Your Gemini API key (optional)                 | For OCR features        |

**To generate a SECRET_KEY**, run this in your terminal:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it as your SECRET_KEY value.

### Step 3.4: Add More Variables (if needed)

If you use OCR/AI features, add these optional variables:

- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `DOCUMENT_AI_PROCESSOR_ID`: Your Document AI processor ID

### Step 3.5: Trigger Redeploy

1. Go to **Deployments** tab
2. **Click** "Redeploy" on the latest deployment
3. **Wait** 3-5 minutes for deployment to complete
4. Watch the logs for any errors

---

## ✅ PHASE 4: Verify Deployment

### Step 4.1: Check Deployment Status

1. In Railway, go to **Deployments** tab
2. Look for ✅ green checkmark (success)
3. If ❌ red X, click on deployment to see error logs

### Step 4.2: Get Your App URL

1. Go to **Settings** tab
2. Find **Domains** section
3. Click **Generate Domain**
4. Railway will give you a URL like: `https://your-app-name.railway.app`

### Step 4.3: Test Your App

1. **Open** your Railway URL in browser
2. **Check** that the homepage loads
3. **Try** logging in (create admin user first - see below)

### Step 4.4: Create Admin User

Since the database is fresh, you need to create an admin user.

**Option A: Using Railway Shell**

1. In Railway, click on your service
2. Click **Shell** tab (or look for terminal icon)
3. Run:

```bash
python manage.py createsuperuser
```

4. Follow prompts to create admin user

**Option B: If Shell isn't available**
You may need to run migrations first. Railway should auto-run them, but if not:

1. Go to **Settings** → **Deploy**
2. Set **Start Command** to:

```
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn section_placement_system.wsgi
```

---

## 🌐 PHASE 5: Custom Domain (Optional)

### Step 5.1: Add Custom Domain in Railway

1. Go to **Settings** tab in your Railway service
2. Find **Domains** section
3. Click **+ Custom Domain**
4. Enter your domain: `enrollment.yourschool.edu.ph`

### Step 5.2: Configure DNS

At your domain registrar (GoDaddy, Namecheap, etc.):

1. **Add CNAME record**:
   - Type: `CNAME`
   - Name: `enrollment` (or `@` for root)
   - Value: `your-app.railway.app`
   - TTL: 3600

2. **Wait** 15-30 minutes for DNS propagation

### Step 5.3: Verify & SSL

1. Railway will automatically provision SSL certificate
2. Your site will be accessible at `https://enrollment.yourschool.edu.ph`

---

## 🔧 PHASE 6: Initial Data Setup

### Step 6.1: Access Django Admin

1. Go to: `https://your-app.railway.app/admin/`
2. Login with your superuser credentials

### Step 6.2: Create Initial Data

In Django Admin, create:

1. **School Year**:
   - Go to Admin App → School Years
   - Add: `2025-2026` (set as active)

2. **Programs**:
   - Go to Admin App → Programs
   - Add your programs: STE, REGULAR, SPFL, SPTVE, OHSP, SNED

3. **Coordinator Accounts**:
   - Go to Admin App → User Profiles
   - Create coordinator accounts for each program

---

## 📊 PHASE 7: Monitoring & Maintenance

### Check Logs

1. Railway Dashboard → Your Service → Deployments → Click deployment → Logs

### Check Database

1. Supabase Dashboard → Table Editor
2. You can view/edit data directly

### Redeploy After Code Changes

1. Push changes to GitHub:

```bash
git add .
git commit -m "Your changes"
git push
```

2. Railway auto-deploys when you push to GitHub!

---

## 🆘 Troubleshooting

### Common Issues:

| Problem                      | Solution                                            |
| ---------------------------- | --------------------------------------------------- |
| "Application Error"          | Check logs in Railway, usually missing env variable |
| "Database connection failed" | Verify DATABASE_URL is correct, no typos            |
| "Static files not loading"   | Run `collectstatic` (should auto-run in Procfile)   |
| "CSRF verification failed"   | Add domain to CSRF_TRUSTED_ORIGINS                  |
| "500 Internal Error"         | Check Railway logs for detailed error               |

### Debug Steps:

1. **Check Railway Logs**:
   - Deployments → Click latest → View logs

2. **Check Environment Variables**:
   - Make sure all required variables are set
   - No extra spaces in values

3. **Test Database Connection**:
   - In Supabase, go to SQL Editor
   - Run: `SELECT 1;` to verify DB is working

---

## 📝 Quick Reference

### Your URLs:

- **App**: `https://your-app.railway.app`
- **Admin**: `https://your-app.railway.app/admin/`
- **Enrollment Form**: `https://your-app.railway.app/enrollment/`
- **Coordinator Login**: `https://your-app.railway.app/coordinator/`

### Environment Variables Needed:

```
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgres://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
DEBUG=False
DJANGO_SETTINGS_MODULE=section_placement_system.settings_production
GEMINI_API_KEY=your-key (optional)
```

### Commands for Local Testing:

```powershell
# Test production settings locally
$env:DJANGO_SETTINGS_MODULE="section_placement_system.settings_production"
$env:DATABASE_URL="your-supabase-url"
$env:SECRET_KEY="test-key"
python manage.py runserver
```

---

## 🎉 Deployment Complete!

Your AI-Based Section Placement System is now live!

**Next Steps:**

1. Create coordinator accounts
2. Set up school year and programs
3. Configure sections
4. Share enrollment link with parents/students
5. Train coordinators on the system

**Support:**

- Railway Docs: https://docs.railway.app
- Supabase Docs: https://supabase.com/docs
- Django Docs: https://docs.djangoproject.com
