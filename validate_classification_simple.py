#!/usr/bin/env python3
"""
Simple validation script for transaction classification without Unicode issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moneymanager.apps.transactions.services import TransactionImportService
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test_classification():
    """Test the enhanced classification logic"""
    service = TransactionImportService()
    
    # Test cases with expected results
    test_cases = [
        # Company payments (should be income)
        ("SAS2PY SOFTWARE P L", 38000.00, "income", "Company payment"),
        ("TECH SOLUTIONS PVT LTD", 50000.00, "income", "Company payment"),
        
        # Person-to-person UPI transfers (should be income)
        ("UPI-MALLIKARJUNA SARMA-9246377264@YBL", 8000.00, "income", "UPI from person"),
        ("UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK", 3000.00, "income", "UPI from person"),
        ("UPI-K SOUDAMINI-SOUDAMINI1220@OKAXIS", 7000.00, "income", "UPI from person"),
        
        # Store/merchant payments (should be expense)
        ("UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI", 10.00, "expense", "UPI to store"),
        ("UPI-PARADISE-PAYTM-80787327@PAYTM", 500.00, "expense", "UPI to merchant"),
        
        # Interest payments (should be income)
        ("INTEREST PAID TILL 30-JUN-2024", 50.00, "income", "Interest payment"),
        
        # ATM withdrawals (should be expense)
        ("ATW-416021XXXXXX2625-P3ENHE44-HYDERABAD", 8000.00, "expense", "ATM withdrawal"),
        ("EAW-416021XXXXXX2625-HYBW9005-EHYDERABAD", 1000.00, "expense", "ATM withdrawal"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    print(f"\nTesting {total} transaction classifications:")
    print("=" * 60)
    
    for i, (description, amount, expected_type, test_type) in enumerate(test_cases, 1):
        # Test HDFC classification
        actual_type = service.determine_transaction_type_hdfc(description, amount)
        
        status = "PASS" if actual_type == expected_type else "FAIL"
        if actual_type == expected_type:
            correct += 1
            
        print(f"{i:2d}. {test_type}")
        print(f"    Description: {description[:50]}...")
        print(f"    Amount: Rs.{amount}")
        print(f"    Expected: {expected_type} | Actual: {actual_type} | {status}")
        print()
    
    accuracy = (correct / total) * 100
    print(f"RESULTS: {correct}/{total} correct ({accuracy:.1f}% accuracy)")
    
    if accuracy == 100:
        print("SUCCESS: All transaction types classified correctly!")
        return True
    else:
        print(f"ISSUES: {total - correct} transactions misclassified")
        return False

if __name__ == "__main__":
    print("Enhanced Transaction Classification Validation")
    print("=" * 50)
    
    success = test_classification()
    
    if success:
        print("\nCONCLUSION: Enhanced classification system working perfectly!")
        print("- Company payments correctly identified as income")
        print("- Person-to-person UPI transfers correctly identified as income") 
        print("- Store/merchant payments correctly identified as expense")
        print("- Interest payments correctly identified as income")
        print("- ATM withdrawals correctly identified as expense")
    else:
        print("\nNEEDS REVIEW: Some classifications need adjustment")
    
    sys.exit(0 if success else 1)