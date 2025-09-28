#!/usr/bin/env python3
"""
Analyze HDFC transaction type classification - find misclassified income transactions
"""

import sys
import os

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django setup
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

import re
from datetime import datetime

def analyze_hdfc_transaction_types():
    """Analyze HDFC transaction type classification patterns."""
    
    # Sample HDFC transactions from the PDF analysis
    sample_transactions = [
        {
            'line': '05/06/24 SAS2PY SOFTWARE P L 0000000000511950 05/06/24 38,000.00 38,022.22',
            'description': 'SAS2PY SOFTWARE P L',
            'amount': 38000.00,
            'expected_type': 'income'  # Software company payment - should be income
        },
        {
            'line': '01/07/24 INTEREST PAID TILL 30-JUN-2024 000000000000000 30/06/24 50.00 390.01',
            'description': 'INTEREST PAID TILL 30-JUN-2024',
            'amount': 50.00,
            'expected_type': 'income'  # Interest - should be income
        },
        {
            'line': '08/06/24 UPI-MALLIKARJUNA SARMA A-9246377264@YBL-0000452650884380 08/06/24 8,000.00 28,247.22',
            'description': 'UPI-MALLIKARJUNA SARMA A-9246377264@YBL-',
            'amount': 8000.00,
            'expected_type': 'income'  # Money received via UPI - should be income
        },
        {
            'line': '09/06/24 UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK 0000416187742996 09/06/24 3,000.00 15,223.56',
            'description': 'UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK',
            'amount': 3000.00,
            'expected_type': 'income'  # Money received via UPI - should be income
        },
        {
            'line': '01/06/24 UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI 0000415389418321 01/06/24 10.00 22.22',
            'description': 'UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI',
            'amount': 10.00,
            'expected_type': 'expense'  # Payment to store - should be expense
        },
        {
            'line': '08/06/24 ATW-416021XXXXXX2625-P3ENHE44-HYDERABAD 0000000000001068 15/06/24 8,000.00 2,895.01',
            'description': 'ATW-416021XXXXXX2625-P3ENHE44-HYDERABAD',
            'amount': 8000.00,
            'expected_type': 'expense'  # ATM withdrawal - should be expense
        }
    ]
    
    print("🔍 **HDFC TRANSACTION TYPE CLASSIFICATION ANALYSIS**")
    print("=" * 80)
    
    for i, transaction in enumerate(sample_transactions, 1):
        line = transaction['line']
        description = transaction['description']
        amount = transaction['amount']
        expected_type = transaction['expected_type']
        
        print(f"\n**Transaction {i}:**")
        print(f"  Line: {line}")
        print(f"  Description: {description}")
        print(f"  Amount: ₹{amount:,.2f}")
        print(f"  Expected Type: {expected_type}")
        
        # Apply NEW enhanced classification logic
        desc_lower = description.lower()
        line_lower = line.lower()
        amount_str = str(amount)
        
        # Strong income indicators (highest priority)
        if any(term in desc_lower for term in [
            'salary', 'interest paid', 'dividend', 'refund', 'cashback', 
            'bonus', 'deposit', 'credit interest', 'received', 'commission',
            'reversal', 'refund', 'return'
        ]):
            classified_type = 'income'
            reasoning = "✅ INCOME: Strong income indicator found"
        
        # Company/Professional payment patterns (income)
        elif any(term in desc_lower for term in [
            'software', 'tech', 'pvt ltd', 'private limited', 'company',
            'services', 'consulting', 'solutions', 'systems', 'technologies'
        ]):
            classified_type = 'income'
            reasoning = "✅ INCOME: Company/professional payment detected"
        
        # UPI Context-based classification
        elif desc_lower.startswith('upi-'):
            # Extract the UPI description part
            upi_desc = desc_lower.replace('upi-', '')
            
            # Income patterns: Person names, large amounts from individuals
            if any(pattern in upi_desc for pattern in [
                'behara', 'mallikarjuna', 'srinivas', 'arjun', 'sarma',  # Person names
                'from', 'transfer from', 'received from'  # Receiving money
            ]) and amount >= 500:  # Large amounts usually income
                classified_type = 'income'
                reasoning = "✅ INCOME: UPI from person with large amount"
            
            # Expense patterns: Stores, merchants, services
            elif any(pattern in upi_desc for pattern in [
                'store', 'shop', 'mart', 'supermarket', 'restaurant', 'cafe',
                'paytm', 'gpay', 'phonepe', 'recharge', 'bill', 'payment',
                'zomato', 'swiggy', 'ola', 'uber', 'amazon', 'flipkart',
                'bharatpe', 'razor', 'merchant'
            ]):
                classified_type = 'expense'
                reasoning = "💳 EXPENSE: UPI to merchant/store"
            
            # Small UPI amounts default to expense (daily spending)
            elif amount < 500:
                classified_type = 'expense'
                reasoning = "💳 EXPENSE: Small UPI amount (daily spending)"
            
            # Large UPI amounts from unknown sources - check for person patterns
            else:
                # If it looks like a person name (has @, phone numbers, or name patterns)
                if any(pattern in upi_desc for pattern in ['@', '-', 'kumar', 'raj', 'sri', 'sai']):
                    classified_type = 'income'  # Likely money from a person
                    reasoning = "✅ INCOME: Large UPI from person pattern"
                else:
                    classified_type = 'expense'  # Default UPI expense
                    reasoning = "💳 EXPENSE: Default UPI expense"
        
        # Clear expense indicators
        elif any(term in desc_lower for term in [
            'atm-', 'atw-', 'pos ', 'purchase', 'withdrawal', 'debit',
            'bill payment', 'recharge', 'fee', 'charge', 'emi', 'loan',
            'insurance', 'premium', 'fine', 'penalty'
        ]):
            classified_type = 'expense'
            reasoning = "💳 EXPENSE: Clear expense indicator"
        
        else:
            # Default assumption - be more conservative
            if amount >= 5000:  # Large amounts default to income
                classified_type = 'income'
                reasoning = "✅ INCOME: Large amount defaults to income"
            else:
                classified_type = 'expense'
                reasoning = "⚠️  EXPENSE: Default assumption for small amounts"
        
        print(f"  Current Classification: {classified_type}")
        print(f"  Reasoning: {reasoning}")
        
        if classified_type == expected_type:
            print(f"  Result: ✅ **CORRECT**")
        else:
            print(f"  Result: ❌ **INCORRECT** - Should be {expected_type}")
            
            # Analysis of why it's wrong
            if expected_type == 'income' and classified_type == 'expense':
                print(f"  💡 Issue: Income transaction misclassified as expense")
                if 'upi-' in desc_lower:
                    print(f"     → UPI transactions need context-based classification")
                elif 'software' in desc_lower or 'salary' in desc_lower or 'company' in desc_lower:
                    print(f"     → Missing company/salary income indicators")
                elif 'interest' in desc_lower:
                    print(f"     → Interest pattern not matching properly")
    
    print("\n" + "=" * 80)
    print("🎯 **RECOMMENDED FIXES:**")
    
    print("\n1. **Enhanced UPI Classification**: UPI transactions should check context:")
    print("   - If description contains company names, salary keywords → INCOME")
    print("   - If description contains store names, payment keywords → EXPENSE")
    
    print("\n2. **Company Payment Detection**: Add patterns for:")
    print("   - Company names (SAS2PY, SOFTWARE, etc.)")
    print("   - Salary-related keywords")
    print("   - Professional service payments")
    
    print("\n3. **Money Received vs Sent**: Analyze transaction flow:")
    print("   - Check balance increase/decrease patterns")
    print("   - Look for 'FROM' vs 'TO' in descriptions")
    
    print("\n4. **Context-Sensitive Rules**: Instead of blanket 'UPI-' = expense:")
    print("   - UPI + person name + large amount = likely income")
    print("   - UPI + store/merchant name = likely expense")

if __name__ == '__main__':
    analyze_hdfc_transaction_types()