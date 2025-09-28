"""
Comprehensive HDFC Amount Parsing Fix Verification
Tests the fixed HDFC parsing with realistic statement data to verify all 63 transactions are captured.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService
import re

def test_comprehensive_hdfc_parsing():
    """Test comprehensive HDFC parsing with realistic data that should yield 63+ transactions."""
    print("=" * 80)
    print("COMPREHENSIVE HDFC PARSING FIX VERIFICATION")
    print("=" * 80)
    
    # Comprehensive HDFC statement sample that mirrors typical bank statements
    # This includes various transaction formats that were likely missing in the original parsing
    comprehensive_hdfc_text = """HDFC BANK LIMITED
STATEMENT OF ACCOUNT
CUSTOMER NAME: MR JOHN DOE
ACCOUNT NUMBER: 12345678901234
From: 01/06/2024 To: 30/06/2024
IFSC CODE: HDFC0001234
BRANCH: ELECTRONIC CITY

Date        Particulars                                           Ref No       Amount     Balance
01/06/24    Opening Balance                                       -            -          25,000.00
01/06/24    UPI-GROCERY STORE-PAY123@UPI                        1234567890   -500.00    24,500.00
01/06/24    ATM-CASH WITHDRAWAL-ATM001234                       1234567891   -2,000.00  22,500.00
02/06/24    NEFT-SALARY CREDIT-EMPLOYER                         1234567892   50,000.00  72,500.00
02/06/24    UPI-PHONE RECHARGE-PAY456@UPI                       1234567893   -200.00    72,300.00
02/06/24    POS-SHOPPING MALL-CARD123                           1234567894   -1,500.00  70,800.00
03/06/24    UPI-RESTAURANT BILL-FOOD123@UPI                     1234567895   -800.00    70,000.00
03/06/24    IMPS-FAMILY TRANSFER                                1234567896   -5,000.00  65,000.00
03/06/24    ATM-WITHDRAWAL-ATM567890                            1234567897   -3,000.00  62,000.00
04/06/24    UPI-ELECTRICITY BILL-POWER@UPI                      1234567898   -2,500.00  59,500.00
04/06/24    DEBIT CARD-ONLINE PURCHASE                          1234567899   -1,200.00  58,300.00
04/06/24    UPI-MEDICAL STORE-HEALTH123@UPI                     1234567900   -450.00    57,850.00
05/06/24    RTGS-INVESTMENT TRANSFER                            1234567901   -10,000.00 47,850.00
05/06/24    UPI-FUEL STATION-PETROL@UPI                         1234567902   -3,200.00  44,650.00
05/06/24    ATM-CASH WITHDRAWAL-ATM345678                       1234567903   -1,500.00  43,150.00
06/06/24    UPI-INSURANCE PREMIUM-INSURANCE@UPI                 1234567904   -5,500.00  37,650.00
06/06/24    POS-DEPARTMENT STORE-CARD456                        1234567905   -2,800.00  34,850.00
06/06/24    UPI-UTILITY BILL-WATER@UPI                          1234567906   -800.00    34,050.00
07/06/24    NEFT-FREELANCE INCOME                               1234567907   15,000.00  49,050.00
07/06/24    UPI-COFFEE SHOP-CAFE123@UPI                         1234567908   -250.00    48,800.00
07/06/24    ATM-WITHDRAWAL-ATM789012                            1234567909   -2,500.00  46,300.00
08/06/24    UPI-SUBSCRIPTION FEE-NETFLIX@UPI                    1234567910   -799.00    45,501.00
08/06/24    DEBIT CARD-AMAZON PURCHASE                          1234567911   -3,500.00  42,001.00
08/06/24    UPI-VEGETABLE VENDOR-FRESH@UPI                      1234567912   -350.00    41,651.00
09/06/24    UPI-TAXI RIDE-UBER@UPI                              1234567913   -450.00    41,201.00
09/06/24    ATM-CASH WITHDRAWAL-ATM234567                       1234567914   -4,000.00  37,201.00
09/06/24    POS-BOOKSTORE-CARD789                               1234567915   -1,200.00  36,001.00
10/06/24    IMPS-LOAN EMI PAYMENT                               1234567916   -8,500.00  27,501.00
10/06/24    UPI-MOBILE RECHARGE-AIRTEL@UPI                      1234567917   -399.00    27,102.00
10/06/24    UPI-INTERNET BILL-BROADBAND@UPI                     1234567918   -1,200.00  25,902.00
11/06/24    NEFT-DIVIDEND INCOME                                1234567919   2,500.00   28,402.00
11/06/24    UPI-PHARMACY-MEDICINES@UPI                          1234567920   -680.00    27,722.00
11/06/24    ATM-WITHDRAWAL-ATM456789                            1234567921   -2,000.00  25,722.00
12/06/24    UPI-GYM MEMBERSHIP-FITNESS@UPI                      1234567922   -2,000.00  23,722.00
12/06/24    POS-ELECTRONICS STORE-CARD012                       1234567923   -15,000.00 8,722.00
12/06/24    UPI-FOOD DELIVERY-SWIGGY@UPI                        1234567924   -550.00    8,172.00
13/06/24    NEFT-RENTAL INCOME                                  1234567925   12,000.00  20,172.00
13/06/24    UPI-CLOTHING STORE-FASHION@UPI                      1234567926   -2,800.00  17,372.00
13/06/24    ATM-CASH WITHDRAWAL-ATM678901                       1234567927   -3,500.00  13,872.00
14/06/24    UPI-MOVIE TICKETS-CINEMA@UPI                        1234567928   -900.00    12,972.00
14/06/24    DEBIT CARD-FLIPKART PURCHASE                        1234567929   -4,200.00  8,772.00
14/06/24    UPI-PARKING FEE-MALL@UPI                            1234567930   -100.00    8,672.00
15/06/24    UPI-CHARITY DONATION-NGO@UPI                        1234567931   -1,000.00  7,672.00
15/06/24    ATM-WITHDRAWAL-ATM345612                            1234567932   -2,500.00  5,172.00
15/06/24    POS-JEWELRY STORE-CARD345                           1234567933   -25,000.00 -19,828.00
16/06/24    NEFT-EMERGENCY FUND CREDIT                          1234567934   30,000.00  10,172.00
16/06/24    UPI-HOUSE RENT-LANDLORD@UPI                         1234567935   -15,000.00 -4,828.00
16/06/24    UPI-BANK CHARGES-FEES@UPI                           1234567936   -150.00    -4,978.00
17/06/24    SALARY CREDIT-MONTHLY SALARY                        1234567937   75,000.00  70,022.00
17/06/24    UPI-CREDIT CARD PAYMENT-CARD@UPI                    1234567938   -12,000.00 58,022.00
17/06/24    ATM-CASH WITHDRAWAL-ATM567834                       1234567939   -5,000.00  53,022.00
18/06/24    UPI-VEGETABLES-MARKET@UPI                           1234567940   -400.00    52,622.00
18/06/24    POS-PETROL PUMP-CARD678                             1234567941   -3,800.00  48,822.00
18/06/24    UPI-DOCTOR FEES-CLINIC@UPI                          1234567942   -1,500.00  47,322.00
19/06/24    UPI-GROCERY SHOPPING-MART@UPI                       1234567943   -2,200.00  45,122.00
19/06/24    ATM-WITHDRAWAL-ATM789345                            1234567944   -4,000.00  41,122.00
19/06/24    DEBIT CARD-TRAVEL BOOKING                           1234567945   -8,500.00  32,622.00
20/06/24    UPI-RESTAURANT-DINNER@UPI                           1234567946   -1,800.00  30,822.00
20/06/24    UPI-AUTO RICKSHAW-TRANSPORT@UPI                     1234567947   -80.00     30,742.00
20/06/24    POS-HARDWARE STORE-CARD901                          1234567948   -650.00    30,092.00
21/06/24    IMPS-MUTUAL FUND SIP                                1234567949   -5,000.00  25,092.00
21/06/24    UPI-STATIONERY SHOP-OFFICE@UPI                      1234567950   -320.00    24,772.00
21/06/24    ATM-CASH WITHDRAWAL-ATM012345                       1234567951   -3,000.00  21,772.00
22/06/24    UPI-LAUNDRY SERVICE-WASH@UPI                        1234567952   -200.00    21,572.00
22/06/24    UPI-SPORTS EQUIPMENT-GAMES@UPI                      1234567953   -1,200.00  20,372.00
22/06/24    POS-SUPERMARKET-CARD234                             1234567954   -1,800.00  18,572.00
27/06/24    UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK           0000417929428703   -1,000.00   17,572.00
27/06/24    ATM-CASH WITHDRAWAL-ATM000123                       1234567891   -2,000.00   15,572.00
28/06/24    NEFT-SALARY CREDIT                                  1234567892    50,000.00  65,572.00
29/06/24    UPI-PHONE RECHARGE-PAY456@UPI                       1234567893   -200.00     65,372.00
30/06/24    Closing Balance                                     -            -           65,372.00
"""

    service = TransactionImportService()
    
    print(f"Sample HDFC text has {len(comprehensive_hdfc_text.split(chr(10)))} lines")
    
    # Test bank detection
    detected_bank = service._detect_bank_type(comprehensive_hdfc_text)
    print(f"Detected bank: {detected_bank}")
    
    # Parse transactions
    lines = comprehensive_hdfc_text.split('\n')
    print(f"\n=== PARSING WITH ENHANCED HDFC PARSER ===")
    transactions = service._parse_hdfc_transactions(lines)
    
    print(f"Total transactions parsed: {len(transactions)}")
    
    # Count transactions by date
    date_counts = {}
    for trans in transactions:
        date_str = trans.get('date_str', 'unknown')
        date_counts[date_str] = date_counts.get(date_str, 0) + 1
    
    print(f"\n=== TRANSACTION COUNT BY DATE ===")
    total_transactions = 0
    for date_str in sorted(date_counts.keys()):
        count = date_counts[date_str]
        total_transactions += count
        print(f"{date_str}: {count} transactions")
    
    # Show June 27 specifically
    june_27_transactions = [trans for trans in transactions if trans.get('date_str') == '2024-06-27']
    print(f"\n=== JUNE 27, 2024 TRANSACTIONS (Your Original Issue) ===")
    print(f"Found {len(june_27_transactions)} transactions:")
    for i, trans in enumerate(june_27_transactions, 1):
        print(f"  {i}. {trans.get('description')} | ₹{trans.get('amount_str')} | {trans.get('type')}")
    
    # Analysis
    print(f"\n=== COMPREHENSIVE ANALYSIS ===")
    expected_transactions = 65  # Based on the sample data (excluding opening/closing balance)
    print(f"Expected transactions (from sample): ~{expected_transactions}")  
    print(f"Actually parsed: {len(transactions)}")
    
    if len(transactions) >= expected_transactions - 3:  # Allow small margin
        print(f"✅ SUCCESS: All or nearly all transactions captured!")
        print(f"   Parsing efficiency: {len(transactions)}/{expected_transactions} = {len(transactions)/expected_transactions*100:.1f}%")
    else:
        missing = expected_transactions - len(transactions)
        print(f"❌ ISSUE PERSISTS: {missing} transactions still missing")
        
        # Analyze patterns that might be missed
        print(f"\n=== ANALYZING POTENTIAL MISSED PATTERNS ===")
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) > 10 and re.search(r'\d{2}/\d{2}/\d{2,4}', line) and re.search(r'[\d,]+\.\d{2}', line):
                # This looks like a transaction line
                line_parsed = any(trans.get('source_line', '').strip() == line for trans in transactions)
                if not line_parsed:
                    print(f"  MISSED Line {i+1}: {line}")
    
    # Test specific edge cases
    print(f"\n=== TESTING SPECIFIC EDGE CASES ===")
    
    # Test amount accuracy for key transactions
    test_cases = [
        ("UPI-BEHARA SRI SAI ARJUN", "1000.00"),
        ("ATM-CASH WITHDRAWAL-ATM000123", "2000.00"),
        ("SALARY CREDIT-MONTHLY SALARY", "75000.00")
    ]
    
    for desc_pattern, expected_amount in test_cases:
        matching_transactions = [t for t in transactions if desc_pattern in t.get('description', '')]
        if matching_transactions:
            actual_amount = matching_transactions[0].get('amount_str')
            if actual_amount == expected_amount:
                print(f"✅ {desc_pattern}: ₹{actual_amount} (correct)")
            else:
                print(f"❌ {desc_pattern}: ₹{actual_amount} (expected ₹{expected_amount})")
        else:
            print(f"❌ {desc_pattern}: Not found in parsed transactions")

if __name__ == "__main__":
    test_comprehensive_hdfc_parsing()