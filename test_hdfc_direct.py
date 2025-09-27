#!/usr/bin/env python
"""
Direct test of HDFC parsing with exact working format
"""
import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')

import django
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService

def test_hdfc_direct():
    """Test HDFC parsing with the exact format that worked before."""
    print("🔍 TESTING HDFC DIRECT PARSING")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Get service
    service = TransactionImportService()
    
    # Use the exact format that worked in our previous test
    hdfc_text = """HDFC BANK
Account Statement for Savings Account 12345678901
Statement Period: 01-Aug-2023 to 31-Aug-2023
Customer Name: Test Customer
Address: Test Address
Account Number: 12345678901

Date        Value Date  Description                                Dr/Cr    Amount      Balance
02/08/23    02/08/23    ATM WITHDRAWAL - MUMBAI                   2000.00  Dr          148000.00
03/08/23    03/08/23    UPI PAYMENT TO MERCHANT                   1500.00  Dr          146500.00
04/08/23    04/08/23    SALARY CREDIT                             50000.00 Cr          196500.00
05/08/23    05/08/23    ONLINE PURCHASE AMAZON                    3500.00  Dr          218000.00
06/08/23    06/08/23    NEFT TRANSFER TO XYZ                      10000.00 Dr          183000.00"""
    
    print("\n1. Testing Bank Detection:")
    bank_type = service._detect_bank_type(hdfc_text)
    print(f"   Detected: {bank_type}")
    
    print("\n2. Testing Transaction Parsing:")
    transactions = service._parse_pdf_transactions(hdfc_text, None)
    print(f"   Found {len(transactions)} transactions")
    
    for i, txn in enumerate(transactions, 1):
        print(f"   {i}. {txn.get('transaction_date', txn.get('date', 'N/A'))} - {txn.get('description', 'N/A')} - ₹{txn.get('amount', '0')} ({txn.get('transaction_type', txn.get('type', 'N/A'))})")
    
    print("\n3. Testing Direct HDFC Method:")
    hdfc_transactions = service._parse_hdfc_transactions(hdfc_text)
    print(f"   HDFC method found {len(hdfc_transactions)} transactions")
    
    for i, txn in enumerate(hdfc_transactions, 1):
        print(f"   {i}. {txn.get('transaction_date', txn.get('date', 'N/A'))} - {txn.get('description', 'N/A')} - ₹{txn.get('amount', '0')} ({txn.get('transaction_type', txn.get('type', 'N/A'))})")
    
    print("\n4. Testing Line-by-Line:")
    lines = hdfc_text.split('\n')
    print("   Analyzing each line:")
    
    for i, line in enumerate(lines):
        if '/' in line and any(char.isdigit() for char in line):
            print(f"   Line {i}: {line}")
    
    print("\n" + "=" * 60)
    print("🎯 HDFC DIRECT TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_hdfc_direct()