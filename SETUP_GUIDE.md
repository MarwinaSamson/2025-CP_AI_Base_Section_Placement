# 🚀 Project Setup & Sharing Guide

## AI-Based Section Placement System

---

## 📋 Table of Contents

1. [Understanding .env Files](#understanding-env-files)
2. [Why We Need .env](#why-we-need-env)
3. [Files to Share vs Files to Keep Private](#files-to-share-vs-files-to-keep-private)
4. [Step-by-Step: Sharing Your Project](#step-by-step-sharing-your-project)
5. [Step-by-Step: Teammate Setup](#step-by-step-teammate-setup)
6. [Troubleshooting](#troubleshooting)

---

## 🔐 Understanding .env Files

### What is a .env file?

A `.env` file is a **configuration file** that stores **sensitive information** and **environment-specific settings** for your application.

**Example of what's inside:**

```
DATABASE_PASSWORD=my_secret_password
GEMINI_API_KEY=your_actual_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/credentials.json
```

### What is .env.example?

`.env.example` is a **template file** showing what variables are needed, but with **placeholder values** instead of real credentials.

**Example:**

```
DATABASE_PASSWORD=your_password_here
GEMINI_API_KEY=your_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

---

## 🎯 Why We Need .env in This Project

### 1. **Security & Privacy**

- ❌ **WITHOUT .env**: Passwords and API keys are hardcoded in files → visible to everyone → **SECURITY RISK**
- ✅ **WITH .env**: Sensitive data is separate → never committed to Git → **SECURE**

**Example of BAD practice (without .env):**

```python
# settings.py - DON'T DO THIS!
DATABASE_PASSWORD = "011304"  # Everyone can see this!
GEMINI_API_KEY = "AIzaSyC9VDG7W..."  # Exposed in Git!
```

**Example of GOOD practice (with .env):**

```python
# settings.py - DO THIS!
import os
DATABASE_PASSWORD = os.getenv('DB_PASSWORD')  # Gets from .env
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Safe & private
```

### 2. **Different Environments**

Each team member has different:

- 📁 File paths: `C:/Users/Marwina/...` vs `C:/Users/Teammate/...`
- 🔑 Passwords: Everyone has their own database password
- 💻 Settings: Local database might be on different ports

### 3. **Easy Configuration**

- ✅ Change settings without modifying code
- ✅ Switch between development/testing/production easily
- ✅ Keep code clean and portable

---

## 📦 Files to Share vs Files to Keep Private

### ✅ FILES TO SHARE (Commit to Git)

| File               | Purpose                                    | Why Share                               |
| ------------------ | ------------------------------------------ | --------------------------------------- |
| `requirements.txt` | Lists all Python packages needed           | Teammates need to install same packages |
| `.env.example`     | Template showing what variables are needed | Shows teammates what to configure       |
| `.gitignore`       | Tells Git what NOT to upload               | Protects sensitive files                |
| `manage.py`        | Django project files                       | Core application code                   |
| `admin_app/`       | Application code                           | Core application code                   |
| `coordinator_app/` | Application code                           | Core application code                   |
| `enrollment_app/`  | Application code                           | Core application code                   |
| `TRAINING_ARC/`    | ML models & code                           | Core application code                   |
| `README.md`        | Project documentation                      | Helps teammates understand project      |

### ❌ FILES TO KEEP PRIVATE (Never Commit)

| File                      | Contains                        | Why Keep Private                        |
| ------------------------- | ------------------------------- | --------------------------------------- |
| `.env`                    | Your actual passwords, API keys | **SECURITY**: Your personal credentials |
| `gemini-ocr-service.json` | Google Cloud credentials        | **SECURITY**: Authentication keys       |
| `db.sqlite3`              | Local database                  | **PERSONAL**: Your local data           |
| `__pycache__/`            | Compiled Python files           | **TEMPORARY**: Auto-generated           |
| `media/`                  | Uploaded files                  | **PERSONAL**: User uploaded content     |
| `*.log`                   | Log files                       | **PERSONAL**: Your local logs           |

---

## 📤 Step-by-Step: Sharing Your Project

### Step 1: Verify .gitignore is Working

```powershell
# Check what files Git will track
git status

# You should NOT see:
# - .env
# - *.json (your credentials)
# - __pycache__/
# - *.log
```

### Step 2: Initialize Git Repository (if not done yet)

```powershell
# Navigate to project folder
cd C:\Users\Marwina\Desktop\Anacondas\AI-Based-Section-placement\2025-CP_AI_Base_Section_Placement

# Initialize Git
git init

# Add all files (except those in .gitignore)
git add .

# Create first commit
git commit -m "Initial commit: AI Section Placement System"
```

### Step 3: Push to GitHub (Recommended Method)

#### Option A: Using GitHub Desktop

1. Open GitHub Desktop
2. Click "Add Local Repository"
3. Select your project folder
4. Click "Publish repository"
5. Choose "Private" repository (important!)
6. Click "Publish Repository"

#### Option B: Using Command Line

```powershell
# Create repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/section-placement-system.git
git branch -M main
git push -u origin main
```

### Step 4: Share with Teammates

**Send them:**

1. 📧 GitHub repository link (or compressed folder)
2. 📄 Setup instructions (the guide below)
3. 📋 List of what they need:
   - PostgreSQL database
   - Google Cloud service account (or share yours if allowed)
   - Gemini API key (or share yours if allowed)

---

## 👥 Step-by-Step: Teammate Setup

### Prerequisites Your Teammates Need:

- ✅ Python 3.8 or higher
- ✅ PostgreSQL database
- ✅ Git installed
- ✅ Code editor (VS Code recommended)

---

### STEP 1: Clone/Download the Project

#### Option A: Clone from GitHub

```powershell
# Open PowerShell/Terminal
cd Desktop

# Clone the repository
git clone https://github.com/YOUR_USERNAME/section-placement-system.git

# Navigate to project
cd section-placement-system
```

#### Option B: Download ZIP

1. Download the project ZIP file
2. Extract to a folder (e.g., `Desktop/section-placement-system`)
3. Open PowerShell in that folder

---

### STEP 2: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# You should see (venv) in your terminal
```

---

### STEP 3: Install Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt

# This will install:
# - Django
# - pandas, numpy, scikit-learn (ML)
# - google-genai, google-cloud-documentai (AI)
# - Pillow, opencv-python (Image processing)
# - And many more...
```

---

### STEP 4: Create .env File

```powershell
# Copy the example file
copy .env.example .env

# Now edit .env with your own values
notepad .env
```

**What to change in .env:**

```ini
# 1. Database Password (change to YOUR password)
DB_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE

# 2. Google Cloud Credentials Path (change to YOUR path)
GOOGLE_APPLICATION_CREDENTIALS=C:/Users/YOUR_NAME/Desktop/api-key/service-account.json

# 3. Gemini API Key (get your own OR use shared key)
GEMINI_API_KEY=YOUR_API_KEY_HERE

# 4. Google Cloud Project (if different)
GOOGLE_CLOUD_PROJECT=your-project-id
```

---

### STEP 5: Setup Google Cloud Credentials

#### Option A: Get Your Own Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Document AI API
4. Create Service Account → Download JSON key
5. Save to `C:/Users/YOUR_NAME/Desktop/api-key/service-account.json`
6. Update path in `.env`

#### Option B: Use Shared Credentials (Ask Team Lead)

1. Ask team lead for the JSON file
2. Save it somewhere safe
3. Update path in `.env` file

---

### STEP 6: Setup Database

```powershell
# 1. Create PostgreSQL database
# Open pgAdmin or command line:

createdb program_recommendation_db
createdb lis_db

# 2. Run Django migrations
python manage.py migrate

# 3. Create superuser account
python manage.py createsuperuser
# Enter username, email, and password when prompted
```

---

### STEP 7: Test the Setup

```powershell
# Run development server
python manage.py runserver

# You should see:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.

# Open browser and go to:
# http://localhost:8000
```

✅ **Success!** If you see the website, everything is working!

---

## 🛠️ Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'django'"

**Solution:**

```powershell
# Make sure virtual environment is activated
venv\Scripts\activate

# Then install requirements
pip install -r requirements.txt
```

---

### Problem: "Database connection error"

**Solution:**

```powershell
# Check PostgreSQL is running
# Check .env file has correct:
# - DB_NAME
# - DB_USER
# - DB_PASSWORD
# - DB_HOST=localhost
# - DB_PORT=5432
```

---

### Problem: "GOOGLE_APPLICATION_CREDENTIALS file not found"

**Solution:**

```ini
# In .env, update to YOUR actual path:
GOOGLE_APPLICATION_CREDENTIALS=C:/Users/YOUR_ACTUAL_NAME/Desktop/api-key/your-file.json

# Make sure:
# 1. File exists at that location
# 2. Use forward slashes (/) not backslashes (\)
# 3. Path is absolute (full path)
```

---

### Problem: ".env file not being read"

**Solution:**

```powershell
# Install python-dotenv if not already
pip install python-dotenv

# Check settings.py has:
from dotenv import load_dotenv
load_dotenv()
```

---

## 📝 Summary for Team Lead (You)

### What You Share:

1. ✅ GitHub repository (or ZIP file)
2. ✅ `requirements.txt`
3. ✅ `.env.example`
4. ✅ This setup guide
5. ✅ Google Cloud credentials (if sharing)

### What You DON'T Share:

1. ❌ Your `.env` file
2. ❌ Your personal API keys (unless intended)
3. ❌ Your local database

### How Teammates Work:

1. They clone your code
2. They create their OWN `.env` file
3. They use their OWN database passwords
4. They may share Google Cloud credentials OR get their own

---

## 🎯 Why This Approach is Professional

### ✅ Security

- Credentials never exposed in code
- Each person has isolated environment
- API keys can be revoked individually

### ✅ Flexibility

- Easy to switch between dev/test/production
- Team members can use different databases
- Easy to update configurations

### ✅ Standard Practice

- This is how professional teams work
- Industry standard for Python/Django projects
- Prepares you for real-world development

---

## 📚 Additional Resources

- **Django Documentation**: https://docs.djangoproject.com
- **python-dotenv**: https://pypi.org/project/python-dotenv/
- **Git & GitHub**: https://docs.github.com
- **PostgreSQL**: https://www.postgresql.org/docs/

---

## ✅ Quick Checklist for Teammates

- [ ] Python installed
- [ ] PostgreSQL installed and running
- [ ] Project cloned/downloaded
- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` completed
- [ ] `.env` file created from `.env.example`
- [ ] `.env` updated with personal credentials
- [ ] Google Cloud credentials file saved
- [ ] Database created
- [ ] `python manage.py migrate` completed
- [ ] `python manage.py createsuperuser` completed
- [ ] `python manage.py runserver` works
- [ ] Can access http://localhost:8000

---

## 🤝 Need Help?

If teammates encounter issues:

1. Check this guide first
2. Verify `.env` file is correct
3. Check PostgreSQL is running
4. Verify virtual environment is activated
5. Ask team lead for assistance

---

**Good luck with your project! 🚀**
