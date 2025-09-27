# SURYA Money Manager - Complete Setup Guide

## 🚀 All Integrations Fixed and Working

This guide will help you set up the SURYA Money Manager application with all integrations properly configured and tested.

## ✅ What's Been Fixed

### 1. **Authentication & User Management**
- ✅ Fixed custom user authentication with email login
- ✅ Added automatic UserProfile creation via signals
- ✅ Improved form validation and error handling
- ✅ Enhanced user registration workflow

### 2. **Family Group Management**
- ✅ Fixed middleware for proper family group context
- ✅ Added caching for better performance
- ✅ Improved group switching with proper error handling
- ✅ Enhanced access control and permissions

### 3. **Transaction Workflow**
- ✅ Added comprehensive signals for account balance updates
- ✅ Improved transaction validation and error handling
- ✅ Fixed bulk import/export functionality
- ✅ Enhanced recurring transaction processing

### 4. **Budget Monitoring System**
- ✅ Fixed budget calculation and alert system
- ✅ Added goal achievement notifications
- ✅ Improved budget analytics and reporting
- ✅ Enhanced category-based budget tracking

### 5. **Portfolio Integration**
- ✅ Fixed price update service with multiple API sources
- ✅ Added comprehensive portfolio analytics
- ✅ Improved holding calculations and performance tracking
- ✅ Enhanced asset management workflows

### 6. **Import/Export Workflows**
- ✅ Completely rewritten import service with better error handling
- ✅ Added support for CSV, Excel formats with validation
- ✅ Improved batch processing for large files
- ✅ Enhanced template generation for imports

### 7. **Background Task System**
- ✅ Added Celery integration with scheduled tasks
- ✅ Created management commands for all operations
- ✅ Implemented automated recurring transactions
- ✅ Added price updates and budget monitoring automation

## 🛠 Prerequisites

1. **Python 3.8+**
2. **Git**
3. **Redis Server** (for Celery/caching)
4. **Database** (SQLite for development, PostgreSQL for production)

## 📦 Quick Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Redis (Windows using Chocolatey)
choco install redis-64

# Or download from: https://redis.io/download
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite by default)
DATABASE_URL=sqlite:///db.sqlite3

# Redis for Celery and Caching
REDIS_URL=redis://localhost:6379/0

# Email Settings (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

# API Keys for Price Updates (optional)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
POLYGON_API_KEY=your-polygon-key
```

### 3. Initialize the System

```bash
# Run the automated initialization script
python initialize_system.py
```

This script will:
- ✅ Run database migrations
- ✅ Create superuser (admin/admin123)
- ✅ Set up default categories
- ✅ Test all integrations
- ✅ Verify system functionality

### 4. Start Services

#### Development Server
```bash
python manage.py runserver
```

#### Background Tasks (Optional)
```bash
# Terminal 1: Start Celery Worker
celery -A moneymanager worker -l info

# Terminal 2: Start Celery Beat (scheduled tasks)
celery -A moneymanager beat -l info

# Terminal 3: Start Redis Server
redis-server
```

## 🔧 Manual Commands Available

### Transaction Management
```bash
# Process recurring transactions
python manage.py process_recurring_transactions

# Process with dry-run
python manage.py process_recurring_transactions --dry-run
```

### Budget Management
```bash
# Update budget amounts
python manage.py update_budget_amounts

# Update with alerts
python manage.py update_budget_amounts --send-alerts

# Update specific budget
python manage.py update_budget_amounts --budget-id <uuid>
```

### Portfolio Management
```bash
# Update all asset prices
python manage.py update_asset_prices

# Update specific symbols
python manage.py update_asset_prices --symbols AAPL GOOGL MSFT

# Update only actively held assets
python manage.py update_asset_prices --active-only

# Force update regardless of last update time
python manage.py update_asset_prices --force
```

## 🎯 Testing the System

### Access Points
- **Application**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Login**: admin / admin123

### Test User Credentials
- **Username**: testuser
- **Email**: test@example.com
- **Password**: testpass123

### Key Features to Test

1. **User Registration & Login**
   - Create new account
   - Email-based login
   - Profile management

2. **Family Group Management**
   - Create family groups
   - Invite members
   - Switch between personal/family context

3. **Account Management**
   - Create accounts (checking, savings, credit, etc.)
   - View account balances
   - Account transaction history

4. **Transaction Management**
   - Add income/expense transactions
   - Create transfers between accounts
   - Set up recurring transactions
   - Bulk import from CSV/Excel

5. **Budget Management**
   - Create budgets with periods
   - Set category allocations
   - Monitor spending alerts
   - Track goals and achievements

6. **Portfolio Management**
   - Create investment portfolios
   - Add holdings with transactions
   - Track performance
   - Monitor asset prices

## 🎉 Success!

Your SURYA Money Manager is now fully integrated and ready to use. All workflows are tested and working:

- ✅ Authentication & User Management
- ✅ Family Group Context Management
- ✅ Transaction Processing & Balance Updates
- ✅ Budget Monitoring & Alerts
- ✅ Portfolio Tracking & Price Updates
- ✅ Import/Export Functionality
- ✅ Background Task Automation
- ✅ Comprehensive Error Handling
- ✅ Performance Optimization

Enjoy managing your finances with a fully integrated system! 💰📊