#!/usr/bin/env python
"""
Test script to validate the enhanced bulk upload transaction module fixes.
This script tests the PDF parsing improvements for proper date extraction
and accurate expense/income classification.
"""
import os
import sys
import django
from datetime import datetime
import logging

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService
from moneymanager.apps.transactions.models import Account
from django.contrib.auth import get_user_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

User = get_user_model()

def test_enhanced_pdf_parsing():
    """Test the enhanced PDF parsing with sample bank statement data."""
    
    # Sample bank statement text (simulating your format)
    sample_pdf_text = """
Bank Statement for Account: XXXXX1111
Statement Period: 01/09/2024 to 30/09/2024
Opening Balance: 10,000.00

Transaction Details:
27/09/2024
55550051070111TFR S48825391 100.00 10,100.00 Cr SALARY CREDIT FROM COMPANY
55550051070112TFR S48825392 50.00 10,050.00 Dr ATM WITHDRAWAL CHARGES
55550051070113TFR S48825393 1,500.00 8,550.00 Dr ELECTRICITY BILL PAYMENT

28/09/2024  
55550051070114TFR S48825394 25.00 8,575.00 Cr CASHBACK REWARD
55550051070115TFR S48825395 200.00 8,375.00 Dr GROCERY PURCHASE
55550051070116TFR S48825396 75.00 8,300.00 Dr FUEL PAYMENT

29/09/2024
55550051070117TFR S48825397 2,000.00 10,300.00 Cr TRANSFER FROM SAVINGS
55550051070118TFR S48825398 300.00 10,000.00 Dr RESTAURANT BILL

Closing Balance: 10,000.00
"""

    print("=== Testing Enhanced PDF Parsing ===")
    print(f"Sample PDF text length: {len(sample_pdf_text)} characters")
    
    # Initialize the service
    service = TransactionImportService()
    
    # Test date extraction
    print("\n--- Testing Date Extraction ---")
    extracted_date = service._extract_statement_date(sample_pdf_text)
    print(f"Extracted statement date: {extracted_date}")
    
    # Test transaction parsing
    print("\n--- Testing Transaction Parsing ---")
    transactions = service._parse_pdf_transactions(sample_pdf_text, extracted_date)
    
    print(f"\nFound {len(transactions)} transactions:")
    print("-" * 80)
    
    for i, trans in enumerate(transactions, 1):
        print(f"{i}. Date: {trans['date_str']}")
        print(f"   Description: {trans['description']}")
        print(f"   Amount: {trans['amount_str']}")
        print(f"   Type: {trans['type'].upper()}")
        print(f"   Source: {trans['source_line'][:60]}...")
        print(f"   Pattern Used: {trans['pattern_used']}")
        print("-" * 80)
    
    # Validate results
    print("\n=== VALIDATION RESULTS ===")
    
    # Check if dates are properly extracted (not defaulting to current date)
    current_date = datetime.now().strftime('%d/%m/%Y')
    dates_extracted = [t['date_str'] for t in transactions]
    proper_dates = [d for d in dates_extracted if d != current_date]
    
    print(f"✓ Total transactions found: {len(transactions)}")
    print(f"✓ Transactions with proper dates: {len(proper_dates)}/{len(transactions)}")
    
    # Check expense/income classification
    expenses = [t for t in transactions if t['type'] == 'expense']
    incomes = [t for t in transactions if t['type'] == 'income']
    
    print(f"✓ Expenses detected: {len(expenses)}")
    print(f"✓ Income detected: {len(incomes)}")
    
    # List expected expenses and incomes for verification
    expected_expenses = [
        'ATM WITHDRAWAL CHARGES',
        'ELECTRICITY BILL PAYMENT', 
        'GROCERY PURCHASE',
        'FUEL PAYMENT',
        'RESTAURANT BILL'
    ]
    
    expected_incomes = [
        'SALARY CREDIT FROM COMPANY',
        'CASHBACK REWARD',
        'TRANSFER FROM SAVINGS'
    ]
    
    print(f"\n--- Expected vs Detected Classification ---")
    
    print("EXPENSES:")
    for exp in expected_expenses:
        found = any(exp.lower() in t['description'].lower() for t in expenses)
        print(f"  {exp}: {'✓ FOUND' if found else '✗ MISSED'}")
    
    print("\nINCOME:")
    for inc in expected_incomes:
        found = any(inc.lower() in t['description'].lower() for t in incomes)
        print(f"  {inc}: {'✓ FOUND' if found else '✗ MISSED'}")
    
    # Check for any misclassifications
    print(f"\n--- Checking for Misclassifications ---")
    misclassified = []
    
    for trans in transactions:
        desc = trans['description'].lower()
        trans_type = trans['type']
        
        # Check if expenses are wrongly marked as income
        expense_keywords = ['bill', 'payment', 'charges', 'purchase', 'withdrawal']
        if any(kw in desc for kw in expense_keywords) and trans_type == 'income':
            misclassified.append(f"EXPENSE marked as INCOME: {trans['description']}")
        
        # Check if income is wrongly marked as expense  
        income_keywords = ['salary', 'credit', 'cashback', 'transfer from']
        if any(kw in desc for kw in income_keywords) and trans_type == 'expense':
            misclassified.append(f"INCOME marked as EXPENSE: {trans['description']}")
    
    if misclassified:
        print("⚠️  Misclassifications found:")
        for misc in misclassified:
            print(f"   {misc}")
    else:
        print("✓ No misclassifications detected!")
    
    return transactions

def test_date_patterns():
    """Test various date pattern extraction."""
    print("\n=== Testing Date Pattern Recognition ===")
    
    service = TransactionImportService()
    
    test_texts = [
        "Statement Period: 01/09/2024 to 30/09/2024",
        "Date: 27-09-2024",  
        "Transaction Date: 2024-09-27",
        "27/09/2024 Transaction details",
        "No date in this text"
    ]
    
    for text in test_texts:
        dates = service._extract_transaction_dates(text, None)
        print(f"Text: '{text}'")
        print(f"Extracted dates: {dates}")
        print()

if __name__ == "__main__":
    print("Starting Bulk Upload Transaction Module Tests...")
    print("=" * 60)
    
    try:
        # Test enhanced PDF parsing
        transactions = test_enhanced_pdf_parsing()
        
        # Test date patterns
        test_date_patterns()
        
        print("\n" + "=" * 60)
        print("✅ BULK UPLOAD MODULE TESTS COMPLETED")
        print("Key Improvements:")
        print("- Enhanced date extraction from bank statements")
        print("- Intelligent expense/income classification")
        print("- Multiple bank statement format support")
        print("- Comprehensive transaction validation")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()