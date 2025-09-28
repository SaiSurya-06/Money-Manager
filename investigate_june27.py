"""
June 27th HDFC Transaction Investigation
Based on the user's report of 2 transactions on June 27th but only 1 being found.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService
import re

def investigate_june_27_issue():
    """Investigate the June 27th missing transaction issue."""
    print("=" * 80)
    print("JUNE 27TH HDFC INVESTIGATION - MISSING TRANSACTION ANALYSIS")
    print("=" * 80)
    
    service = TransactionImportService()
    
    # Let's simulate what the ACTUAL PDF might contain based on user report
    print("Based on the logs, we found only 1 transaction on June 27th:")
    print("  Line 294: 27/06/24 UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK 0000417929428703 27/06/24 1,000.00 1,340.01")
    print()
    print("But user reports there should be 2 transactions on June 27th.")
    print("Let's investigate potential issues:")
    
    print("\n=== HYPOTHESIS 1: Multi-line transaction split ===")
    # Sometimes HDFC transactions span multiple lines due to long descriptions
    multiline_test = """27/06/24 UPI-BEHARA SRI SAI 
ARJUN-SAIARJUN1202@OK 0000417929428703 27/06/24 1,000.00 1,340.01
27/06/24 ATM-CASH WITHDRAWAL
FROM ATM LOCATION 0000000000002279 27/06/24 2,000.00 -660.01"""
    
    print(f"Testing multi-line scenario:")
    lines = multiline_test.strip().split('\n')
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: {line}")
    
    transactions = service._parse_hdfc_transactions(lines)
    print(f"\nParsed {len(transactions)} transactions from multi-line test:")
    for i, trans in enumerate(transactions, 1):
        print(f"  {i}. {trans.get('description')} = ₹{trans.get('amount_str')}")
    
    print("\n=== HYPOTHESIS 2: Different transaction formats ===")
    # Maybe the second transaction has a different format
    different_format_test = """27/06/24 UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK 0000417929428703 27/06/24 1,000.00 1,340.01
27/06/24 ATM WDL TXN/P3ENHE44/HYDERABAD ATM 0000000000002279 27/06/24 2,000.00 -660.01
27/06/24 DEBIT CARD TXN 416021XXXXXX2625 MERCHANT POS 27/06/24 500.00 -1,160.01"""
    
    print(f"Testing different formats:")
    lines = different_format_test.strip().split('\n')
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: {line}")
    
    transactions = service._parse_hdfc_transactions(lines)
    print(f"\nParsed {len(transactions)} transactions from different format test:")
    for i, trans in enumerate(transactions, 1):
        print(f"  {i}. {trans.get('description')} = ₹{trans.get('amount_str')}")
    
    print("\n=== HYPOTHESIS 3: Transaction on next line ===")
    # Maybe there's a transaction immediately after that we're missing
    next_line_test = """27/06/24 UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK 0000417929428703 27/06/24 1,000.00 1,340.01
SBI-SBIN0020312-417929428703-UPI
27/06/24 ATM-CASH WITHDRAWAL-ATM000123 1234567891 27/06/24 2,000.00 -660.01"""
    
    print(f"Testing adjacent line scenario:")
    lines = next_line_test.strip().split('\n')
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: {line}")
    
    transactions = service._parse_hdfc_transactions(lines)
    print(f"\nParsed {len(transactions)} transactions from adjacent line test:")
    for i, trans in enumerate(transactions, 1):
        print(f"  {i}. {trans.get('description')} = ₹{trans.get('amount_str')}")
    
    print("\n=== HYPOTHESIS 4: Missing due to PDF text extraction ===")
    # Maybe the PDF has formatting issues
    print("Possible causes of missing transactions:")
    print("1. PDF text extraction splits transaction across lines")
    print("2. Special characters or formatting in PDF cause parsing failure")
    print("3. Transaction has unusual format not covered by regex patterns")
    print("4. Balance becomes negative causing different parsing behavior")
    
    print("\n=== RECOMMENDATION ===")
    print("To identify the exact issue, we need:")
    print("1. The raw text from the PDF around June 27th")
    print("2. Check if there are any lines between line 294 and 295 in the actual PDF")
    print("3. Verify if any transactions have negative balances or unusual formats")
    
    return transactions

def check_negative_balance_parsing():
    """Test how negative balances are handled."""
    print("\n" + "=" * 80)
    print("NEGATIVE BALANCE TRANSACTION PARSING TEST")
    print("=" * 80)
    
    service = TransactionImportService()
    
    # Test negative balance scenarios
    negative_balance_test = """26/06/24 UPI-PREVIOUS TRANSACTION 1234567890 26/06/24 500.00 2,000.01
27/06/24 UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK 0000417929428703 27/06/24 1,000.00 1,000.01
27/06/24 ATM-CASH WITHDRAWAL-ATM000123 1234567891 27/06/24 2,000.00 -999.99
28/06/24 UPI-NEXT TRANSACTION 1234567892 28/06/24 300.00 -1,299.99"""
    
    lines = negative_balance_test.strip().split('\n')
    print("Testing with negative balances:")
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: {line}")
    
    transactions = service._parse_hdfc_transactions(lines)
    print(f"\nParsed {len(transactions)} transactions:")
    
    june_27_transactions = []
    for i, trans in enumerate(transactions, 1):
        date_str = trans.get('date_str', 'Unknown')
        if '27' in date_str and '06' in date_str:
            june_27_transactions.append(trans)
            print(f"  June 27: {trans.get('description')} = ₹{trans.get('amount_str')}")
        else:
            print(f"  Other: {date_str} - {trans.get('description')} = ₹{trans.get('amount_str')}")
    
    print(f"\nJune 27 transactions found: {len(june_27_transactions)}")
    
    if len(june_27_transactions) < 2:
        print("❌ Still missing June 27 transactions!")
        
        # Manual regex test
        print("\nManual pattern testing on problematic lines:")
        for line in lines:
            if '27/06/24' in line:
                print(f"\nTesting line: {line}")
                
                # Test all HDFC patterns
                patterns = [
                    r'^(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(\d{10,})\s+\d{2}/\d{2}/\d{2}\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    r'^(\d{2}/\d{2}/\d{2})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    r'^(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(\d{8,})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(\d{8,})\s+(-?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    r'^(\d{2}/\d{2}/\d{2,4})\s+(UPI-|ATM|ATW|POS).+?\s+(\d{8,})\s+(-?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(-?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    r'^(\d{2}/\d{2}/\d{2,4})\s+(.+)$'
                ]
                
                pattern_matched = False
                for i, pattern in enumerate(patterns, 1):
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        print(f"  ✅ Matches Pattern {i}")
                        print(f"     Groups: {match.groups()}")
                        pattern_matched = True
                        break
                
                if not pattern_matched:
                    print(f"  ❌ NO PATTERNS MATCH!")
    else:
        print("✅ Both June 27 transactions found!")

if __name__ == "__main__":
    investigate_june_27_issue()
    check_negative_balance_parsing()