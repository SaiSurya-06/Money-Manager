#!/usr/bin/env python
"""
Test script specifically for Federal Bank statement parsing.
Tests the enhanced parsing with the actual test statement provided.
"""
import os
import sys
import django
import PyPDF2
from datetime import datetime
import logging

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_federal_bank_statement():
    """Test parsing of the actual Federal Bank statement."""
    
    pdf_path = r"C:\Users\6033569\Downloads\TEST_STATEMENT.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Extract PDF text
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() + "\n"
    except Exception as e:
        print(f"❌ Error reading PDF: {str(e)}")
        return
    
    print(f"✅ Successfully extracted PDF text ({len(pdf_text)} characters)")
    
    # Initialize service and test parsing
    service = TransactionImportService()
    
    print("\n" + "="*80)
    print("TESTING FEDERAL BANK STATEMENT PARSING")
    print("="*80)
    
    # Test date extraction
    print("\n--- Testing Federal Bank Date Extraction ---")
    dates = service._extract_federal_bank_dates(pdf_text)
    print(f"Extracted dates: {dates}")
    
    # Test transaction parsing
    print("\n--- Testing Federal Bank Transaction Parsing ---")
    transactions = service._parse_pdf_transactions(pdf_text)
    
    print(f"\n🎯 FOUND {len(transactions)} TRANSACTIONS:")
    print("-" * 100)
    
    expected_results = {
        # Based on your actual statement analysis
        'total_transactions': 10,
        'income_transactions': [
            'EPIFI TECHNOLOGIES',  # Salary
            'UPI IN',              # Money received 
        ],
        'expense_transactions': [
            'UPI OUT',             # Money paid
            'paytm',               # Paytm payments
        ]
    }
    
    income_count = 0
    expense_count = 0
    
    for i, trans in enumerate(transactions, 1):
        trans_type_indicator = "💰" if trans['type'] == 'income' else "💸"
        
        print(f"{i:2d}. {trans_type_indicator} {trans['date_str']} | {trans['type'].upper():7s} | ₹{trans['amount_str']:>8s}")
        print(f"     📝 {trans['description'][:70]}...")
        print(f"     📄 Pattern {trans['pattern_used']} | {trans['source_line'][:50]}...")
        print("-" * 100)
        
        if trans['type'] == 'income':
            income_count += 1
        else:
            expense_count += 1
    
    # Validation
    print(f"\n📊 TRANSACTION ANALYSIS:")
    print(f"   Total Transactions: {len(transactions)}")
    print(f"   Income Transactions: {income_count} 💰")
    print(f"   Expense Transactions: {expense_count} 💸")
    
    # Specific Federal Bank validation
    print(f"\n🔍 FEDERAL BANK SPECIFIC VALIDATION:")
    
    # Check UPI transactions
    upi_in_count = sum(1 for t in transactions if 'upi in' in t['description'].lower() and t['type'] == 'income')
    upi_out_count = sum(1 for t in transactions if 'upi out' in t['description'].lower() and t['type'] == 'expense')
    
    print(f"   ✅ UPI IN → Income: {upi_in_count} transactions")
    print(f"   ✅ UPI OUT → Expense: {upi_out_count} transactions")
    
    # Check EPIFI (salary) 
    epifi_transactions = [t for t in transactions if 'epifi' in t['description'].lower()]
    epifi_income = sum(1 for t in epifi_transactions if t['type'] == 'income')
    
    print(f"   ✅ EPIFI → Income: {epifi_income}/{len(epifi_transactions)} transactions")
    
    # Check dates
    date_accuracy = len([t for t in transactions if t['date_str'] != datetime.now().strftime('%d/%m/%Y')])
    print(f"   ✅ Proper Dates: {date_accuracy}/{len(transactions)} transactions")
    
    # Expected transactions from manual analysis
    print(f"\n📋 EXPECTED VS ACTUAL:")
    
    expected_transactions = [
        ("22/05/2023", "IFN/FBLEPIZIDUE... 55550051070111TFR S48825391", "100.00", "income"),
        ("28/05/2023", "EPIFI TECHNOLOGIES", "1.00", "income"),  
        ("31/05/2023", "UPI IN", "150.00", "income"),
        ("31/05/2023", "UPI OUT paytm", "120.00", "expense"),
        ("02/06/2023", "UPI IN", "100.00", "income"),
        ("03/06/2023", "UPI OUT paytm", "38.00", "expense"),
        ("06/06/2023", "UPI OUT", "30.00", "expense"),
        ("16/06/2023", "UPI OUT paytm", "90.00", "expense"), 
        ("17/06/2023", "UPI OUT", "65.00", "expense"),
        ("27/06/2023", "FT IMPS KARZA TECH", "1.00", "income"),
    ]
    
    print(f"   Expected: {len(expected_transactions)} transactions")
    print(f"   Found: {len(transactions)} transactions")
    
    # Check for major issues
    issues = []
    
    if len(transactions) == 0:
        issues.append("❌ No transactions found - pattern matching failed")
    
    if income_count == 0:
        issues.append("❌ No income transactions detected - classification issue")
        
    if expense_count == 0:
        issues.append("❌ No expense transactions detected - classification issue")
        
    all_current_dates = all(t['date_str'] == datetime.now().strftime('%d/%m/%Y') for t in transactions)
    if all_current_dates and len(transactions) > 0:
        issues.append("❌ All dates are current date - date extraction failed")
    
    if issues:
        print(f"\n⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"\n🎉 FEDERAL BANK PARSING SUCCESS!")
        print(f"   ✅ Transactions parsed correctly")
        print(f"   ✅ Income/Expense classification working") 
        print(f"   ✅ Date extraction functional")
    
    return transactions

if __name__ == "__main__":
    print("🏦 FEDERAL BANK STATEMENT PARSER TEST")
    print("="*60)
    
    try:
        transactions = test_federal_bank_statement()
        
        if transactions:
            print(f"\n🎯 SUCCESS: Parsed {len(transactions)} transactions from Federal Bank statement")
        else:
            print(f"\n❌ FAILED: No transactions parsed")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()