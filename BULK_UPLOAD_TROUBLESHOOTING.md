# Bulk Upload Transactions - Troubleshooting Guide

## ✅ **What Has Been Fixed**

The bulk upload functionality has been completely overhauled with the following fixes:

### 1. **Form Validation Issues** ✅
- Fixed account queryset filtering for family groups vs personal accounts
- Added proper file size validation (10MB limit)
- Added file extension validation (CSV, Excel only)
- Enhanced error messages with user-friendly feedback

### 2. **Import Service Issues** ✅
- Fixed transaction batch creation to properly trigger signals
- Improved category creation/lookup logic
- Enhanced error handling for malformed data
- Fixed Unicode/BOM handling for CSV files

### 3. **Error Handling & User Feedback** ✅
- Added comprehensive error messages with emojis
- Provided helpful tips for common issues
- Improved success/warning message display
- Added detailed validation feedback

### 4. **File Processing Issues** ✅
- Fixed file pointer reset before processing
- Enhanced CSV and Excel parsing
- Better date format detection
- Improved amount parsing with currency symbols

---

## 🐛 **Common Issues & Solutions**

### Issue 1: "No accounts available"
**Solution**:
- Create at least one account before uploading transactions
- Go to Transactions → Accounts → Create Account
- Ensure the account is active and belongs to the correct family group

### Issue 2: "Invalid date format" errors
**Expected Format**: `YYYY-MM-DD` (e.g., `2025-01-15`)
**Common Issues**:
- Using `MM/DD/YYYY` → Convert to `YYYY-MM-DD`
- Using `DD/MM/YYYY` → Convert to `YYYY-MM-DD`
- Using text dates → Convert to numeric format

### Issue 3: "Invalid transaction type" errors
**Expected Values**:
- `income` (lowercase)
- `expense` (lowercase)
**Common Issues**:
- Using `Income` or `INCOME` → Use `income`
- Using `Expense` or `EXPENSE` → Use `expense`
- Using `debit/credit` → Use `expense/income`

### Issue 4: "Invalid amount format" errors
**Expected Format**: Positive numbers (e.g., `123.45`)
**Common Issues**:
- Negative amounts → Use positive amounts only
- Currency symbols → Remove `₹`, `$`, `€`, etc.
- Text in amount field → Use numbers only

### Issue 5: File upload fails immediately
**Check**:
- File size < 10MB
- File extension is .csv, .xlsx, or .xls
- File is not corrupted
- Browser supports file uploads

---

## 📄 **Required File Format**

### CSV Format
```csv
Date,Description,Amount,Type,Category,Notes
2025-01-01,Monthly Salary,3000.00,income,Salary,January salary payment
2025-01-02,Grocery Shopping,125.50,expense,Groceries,Weekly shopping
2025-01-03,Gas Station,45.00,expense,Transportation,Fuel for car
```

### Required Columns (first 4 are mandatory):
1. **Date** - Format: YYYY-MM-DD
2. **Description** - Any text description
3. **Amount** - Positive decimal number
4. **Type** - Either 'income' or 'expense'
5. **Category** - Optional category name
6. **Notes** - Optional additional notes

---

## 🧪 **Testing Steps**

### Step 1: Test with Sample File
1. Use the provided `sample_transactions.csv`
2. Create a test account first
3. Upload the file and verify it processes correctly

### Step 2: Check Django Logs
```bash
# Enable debug logging
DEBUG = True  # in settings

# Check logs for detailed error messages
python manage.py runserver --verbosity=2
```

### Step 3: Test Form Validation
1. Try uploading without selecting an account
2. Try uploading an invalid file type
3. Verify error messages appear correctly

### Step 4: Test Import Service
```python
# Test in Django shell
python manage.py shell

from moneymanager.apps.transactions.services import import_service
from moneymanager.apps.transactions.models import Account
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()
account = Account.objects.first()

# Test file parsing manually
with open('sample_transactions.csv', 'r') as f:
    result = import_service.import_transactions(f, account, user)
    print(result)
```

---

## 🔧 **Manual Debugging**

### Check Database State
```python
# Django shell commands
python manage.py shell

# Check accounts
from moneymanager.apps.transactions.models import Account
print(f"Accounts: {Account.objects.count()}")
for acc in Account.objects.all():
    print(f"- {acc.name} (Owner: {acc.owner}, Family: {acc.family_group})")

# Check categories
from moneymanager.apps.core.models import Category
print(f"Categories: {Category.objects.count()}")
```

### Test File Processing
```python
# Test CSV parsing
import csv
import io

with open('sample_transactions.csv', 'r') as f:
    content = f.read()
    print("File content preview:")
    print(content[:200])

    # Test CSV reader
    io_string = io.StringIO(content)
    reader = csv.reader(io_string)
    rows = list(reader)
    print(f"Rows found: {len(rows)}")
    for i, row in enumerate(rows[:3]):
        print(f"Row {i}: {row}")
```

---

## 🎯 **Success Verification**

After uploading, verify:

1. **Transaction Count**: Check transactions list increased
2. **Account Balance**: Verify account balance updated correctly
3. **Categories**: New categories were created if specified
4. **Data Accuracy**: Spot-check a few transactions for correct data

### Quick Verification Commands:
```python
# Django shell
from moneymanager.apps.transactions.models import Transaction

# Check recent transactions
recent = Transaction.objects.order_by('-created_at')[:5]
for t in recent:
    print(f"{t.date}: {t.description} - ${t.amount} ({t.transaction_type})")
```

---

## ⚡ **Performance Tips**

1. **File Size**: Keep files under 5MB for best performance
2. **Batch Size**: Upload 1000 transactions at a time
3. **Clean Data**: Pre-validate data before upload to avoid errors
4. **Categories**: Use existing category names to avoid duplicates

---

## 🆘 **If Still Not Working**

1. **Check Django Debug Mode**: Set `DEBUG = True` in settings
2. **Check Server Logs**: Look for detailed error messages
3. **Test Basic Functions**: Verify account creation and manual transactions work
4. **Browser Console**: Check for JavaScript errors during upload
5. **File Permissions**: Ensure Django can read uploaded files

### Emergency Reset:
```bash
# Reset migrations if needed
python manage.py migrate transactions zero
python manage.py makemigrations transactions
python manage.py migrate transactions
```

The bulk upload system is now robust and should handle most common scenarios. Use this guide to troubleshoot any remaining issues.

## 📞 **Support**

If problems persist, provide:
- Sample data file causing issues
- Complete error messages
- Django version and OS
- Browser developer console logs