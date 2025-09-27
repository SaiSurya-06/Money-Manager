# MoneyManager - Personal Finance Management System

A comprehensive Django-based personal finance management web application with **advanced multi-bank statement parsing**, family group sharing capabilities, and intelligent transaction processing. Built following Django 5.x best practices.

## 🚀 Latest Features - Multi-Bank Statement Parsing

### 🏦 Supported Banks
- ✅ **Federal Bank**: Complete parsing with DD-MMM-YYYY date conversion and balance-based classification
- ✅ **SBI (State Bank of India)**: Full support with DD-MM-YY format and debit/credit column detection  
- ✅ **HDFC Bank**: Detection implemented, parsing framework ready
- ✅ **Generic Banks**: Fallback parsing for unknown statement formats

### 💡 Key Improvements
- **Fixed Date Parsing**: Resolved DD/MM vs MM/DD conflicts (02/06/2023 = June 2nd, not February 6th)
- **Accurate Transaction Types**: Smart expense/income classification using balance changes
- **Enhanced PDF Processing**: Robust text extraction with intelligent pattern matching
- **Comprehensive Testing**: Full test coverage for all parsing scenarios

## Features

### 🔐 **User Authentication & Family Groups**
- Secure user registration and login system
- Custom user model with extended profile fields
- Family group creation and management
- Role-based permissions (Admin, Member, Viewer)
- Email verification and password reset

### 💰 **Transaction Management**
- Complete CRUD operations for transactions
- Support for Income, Expense, and Transfer types
- Category-based organization with color coding
- Account management with balance tracking
- Receipt attachment support
- Bulk transaction import via CSV
- Advanced filtering and search capabilities

### 🏦 **Account Management**
- Multiple account types (Checking, Savings, Credit, Investment, etc.)
- Real-time balance calculations
- Account grouping and organization
- Transaction history per account

### 📊 **Dashboard & Analytics**
- Interactive dashboard with financial overview
- Real-time charts and visualizations using Chart.js
- Monthly trends and spending analysis
- Category-wise expense breakdown
- Account balance summaries

### 🎯 **Budget Management**
- Flexible budget creation (Weekly, Monthly, Quarterly, Yearly)
- Category-based budget allocation
- Progress tracking with visual indicators
- Budget alerts and notifications
- Variance analysis and reporting

### 🎯 **Financial Goals**
- Goal creation and tracking
- Progress monitoring
- Multiple goal types (Savings, Debt Payoff, Purchase, etc.)
- Target date and priority management

### 📱 **Responsive Design**
- Modern Bootstrap 5 interface
- Mobile-first responsive design
- Dark mode support
- Accessibility features
- Progressive Web App (PWA) capabilities

## Technology Stack

- **Backend**: Django 5.x, Python 3.9+
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Frontend**: Bootstrap 5, Chart.js, Vanilla JavaScript
- **Authentication**: Django's built-in authentication system
- **File Processing**: Pillow, PyPDF2, openpyxl
- **Task Queue**: Celery with Redis
- **Deployment**: Gunicorn, WhiteNoise

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SURYA-Money-Manager
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env file with your settings
   # Generate a new SECRET_KEY for production
   ```

5. **Database setup**
   ```bash
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate

   # Create initial data (categories, etc.)
   python manage.py setup_initial_data

   # Create superuser
   python manage.py createsuperuser
   ```

6. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser to `http://127.0.0.1:8000`
   - Admin panel: `http://127.0.0.1:8000/admin`

### Production Deployment

1. **Environment Setup**
   - Set `DEBUG=False` in production
   - Configure proper database (PostgreSQL recommended)
   - Set up email backend for notifications
   - Configure Redis for Celery (optional)

2. **Security Settings**
   ```bash
   # Generate strong secret key
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Database Migration**
   ```bash
   python manage.py migrate --settings=moneymanager.settings.production
   python manage.py collectstatic --settings=moneymanager.settings.production
   ```

4. **Web Server Configuration**
   ```bash
   # Using Gunicorn
   gunicorn moneymanager.wsgi:application --bind 0.0.0.0:8000
   ```

## Project Structure

```
moneymanager/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
├── static/                     # Static files (CSS, JS, images)
├── media/                      # User uploaded files
├── templates/                  # HTML templates
├── logs/                       # Application logs
├── moneymanager/              # Main project directory
│   ├── __init__.py
│   ├── settings/              # Settings modules
│   │   ├── base.py           # Base settings
│   │   ├── local.py          # Development settings
│   │   └── production.py     # Production settings
│   ├── urls.py               # URL configuration
│   ├── wsgi.py              # WSGI configuration
│   ├── celery.py            # Celery configuration
│   └── apps/                # Django applications
│       ├── core/            # Core functionality
│       ├── accounts/        # User management
│       ├── transactions/    # Transaction management
│       ├── budgets/        # Budget & goals
│       ├── portfolios/     # Investment tracking
│       ├── dashboard/      # Dashboard views
│       └── imports/        # Data import functionality
```

## API Documentation

### Family Group Management
- Switch between personal and family group contexts
- Manage family members and permissions
- Data isolation between groups

### Transaction Operations
- GET `/transactions/` - List transactions with filtering
- POST `/transactions/create/` - Create new transaction
- PUT `/transactions/<id>/` - Update transaction
- DELETE `/transactions/<id>/` - Delete transaction (soft delete)

### Account Management
- GET `/transactions/accounts/` - List all accounts
- POST `/transactions/accounts/create/` - Create new account
- GET `/transactions/accounts/<id>/` - Account details with transactions

### Budget Operations
- GET `/budgets/` - List budgets with progress
- POST `/budgets/create/` - Create new budget
- GET `/budgets/<id>/` - Budget details with analytics

## Key Features Explanation

### Family Group Sharing
- Create family groups to share financial data
- Different permission levels (Admin, Member, Viewer)
- Switch between personal and family contexts
- Data isolation ensures privacy

### Smart Categorization
- Pre-defined category system with icons and colors
- Custom category creation
- Automatic categorization suggestions (future feature)
- Hierarchical category structure

### Advanced Filtering
- Multi-criteria transaction filtering
- Date range selection with presets
- Account-specific filtering
- Category and amount-based searches

### Visual Analytics
- Interactive charts using Chart.js
- Spending trends and patterns
- Budget vs actual comparisons
- Category distribution analysis

## Security Features

- CSRF protection on all forms
- SQL injection prevention
- XSS protection
- Secure password hashing
- Session security
- File upload validation
- Data access controls

## Performance Optimizations

- Database query optimization with select_related/prefetch_related
- Static file compression and caching
- Image optimization for receipts
- Pagination for large datasets
- Efficient data aggregation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Testing

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test moneymanager.apps.transactions

# Coverage report
coverage run --source='.' manage.py test
coverage html
```

## Support & Documentation

- **Issues**: Report bugs and feature requests via GitHub issues
- **Documentation**: Additional documentation in `/docs` directory
- **Email**: support@moneymanager.com (if applicable)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django framework and community
- Bootstrap for responsive design
- Chart.js for data visualization
- Font Awesome and Bootstrap Icons
- All open-source contributors

---

**MoneyManager** - Take control of your finances with intelligent tracking, budgeting, and analytics.