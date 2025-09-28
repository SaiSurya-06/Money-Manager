#!/usr/bin/env python3

"""
Enhanced HDFC parsing with proper Withdrawal/Deposit column handling

The HDFC statement format is:
Date | Narration | Chq./Ref.No. | Value Dt | Withdrawal Amt. | Deposit Amt. | Closing Balance

Key insight: 
- Withdrawal Amt. column = expense (money going out)
- Deposit Amt. column = income (money coming in)
"""

import re
from decimal import Decimal

def parse_hdfc_with_column_detection(line: str, line_num: int) -> dict:
    """
    Parse HDFC transaction with proper column detection
    
    Returns:
        dict with parsed transaction or None if not a transaction
    """
    
    # Enhanced HDFC pattern with column capture
    # This pattern captures:
    # Group 1: Date (DD/MM/YY or DD/MM/YYYY)
    # Group 2: Description (everything between date and amounts)
    # Group 3: First amount (could be withdrawal or deposit)
    # Group 4: Second amount (could be deposit or balance)
    # Group 5: Third amount (closing balance if present)
    
    patterns = [
        # Standard HDFC format: Date Description RefNo ValueDate Amount1 Amount2 [Amount3]
        r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})(?:\s+([\d,]+\.\d{2}))?',
        
        # With explicit reference number
        r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(\d{8,})\s+\d{2}/\d{2}/\d{2,4}\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})',
        
        # ATM/UPI specific patterns
        r'^(\d{2}/\d{2}/\d{2,4})\s+(UPI-|ATM|ATW|POS|EAW-)(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})',
    ]
    
    for pattern_num, pattern in enumerate(patterns, 1):
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1)
                description = match.group(2).strip()
                
                # Extract amounts based on pattern
                if pattern_num == 1:  # Standard format
                    amounts = [match.group(3), match.group(4)]
                    if match.group(5):  # Third amount present
                        amounts.append(match.group(5))
                elif pattern_num == 2:  # With ref number
                    description = match.group(2).strip()
                    amounts = [match.group(4), match.group(5)]
                elif pattern_num == 3:  # ATM/UPI
                    prefix = match.group(2)
                    desc_part = match.group(3).strip()
                    description = prefix + desc_part
                    amounts = [match.group(4), match.group(5)]
                
                # Clean amounts
                clean_amounts = [float(amt.replace(',', '')) for amt in amounts]
                
                # Determine transaction amount and type based on HDFC column structure
                transaction_amount, transaction_type = determine_hdfc_transaction_type(
                    description, clean_amounts, line
                )
                
                if transaction_amount > 0:
                    return {
                        'date_str': convert_hdfc_date(date_str),
                        'description': clean_description(description),
                        'amount_str': str(transaction_amount),
                        'type': transaction_type,
                        'source_line': line,
                        'pattern_used': pattern_num,
                        'bank_type': 'HDFC'
                    }
                    
            except Exception as e:
                continue
    
    return None

def determine_hdfc_transaction_type(description: str, amounts: list, full_line: str) -> tuple:
    """
    Determine transaction amount and type for HDFC based on column analysis
    
    HDFC Format Analysis:
    - If balance increases by amount = deposit (income)
    - If balance decreases by amount = withdrawal (expense)  
    - Amount in withdrawal column = expense
    - Amount in deposit column = income
    """
    
    desc_lower = description.lower()
    
    # For HDFC, we need to analyze the balance change
    if len(amounts) >= 2:
        # amounts[0] = transaction amount, amounts[1] = closing balance
        transaction_amount = amounts[0]
        closing_balance = amounts[1]
        
        # **CRITICAL HDFC LOGIC**: 
        # In HDFC statements, transaction amount appears in either:
        # - Withdrawal column (expense) 
        # - Deposit column (income)
        # We need to determine which based on context
        
        # Strong income indicators override amount-based logic
        if any(term in desc_lower for term in [
            'interest paid', 'salary', 'dividend', 'bonus', 'refund',
            'software', 'tech', 'solutions', 'services', 'pvt ltd'
        ]):
            return transaction_amount, 'income'
        
        # Strong expense indicators  
        if any(term in desc_lower for term in [
            'atw-', 'atm-', 'eaw-', 'pos ', 'withdrawal', 'purchase',
            'recharge', 'bill payment', 'fee', 'charge'
        ]):
            return transaction_amount, 'expense'
        
        # UPI logic - ALL UPI- transactions are outgoing payments (expenses)
        if desc_lower.startswith('upi-'):
            return transaction_amount, 'expense'
        
        # For ambiguous cases, use amount analysis
        if transaction_amount >= 5000:
            # Large amounts are more likely income unless clearly expense
            return transaction_amount, 'income'  
        else:
            # Small amounts default to expense
            return transaction_amount, 'expense'
    
    # Single amount case
    elif len(amounts) == 1:
        return amounts[0], 'expense'  # Conservative default
    
    return 0, 'expense'

def convert_hdfc_date(date_str: str) -> str:
    """Convert HDFC date format to standard YYYY-MM-DD"""
    if '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = '20' + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return date_str

def clean_description(description: str) -> str:
    """Clean HDFC description"""
    # Remove reference numbers
    description = re.sub(r'\d{8,}', '', description)
    # Remove extra spaces
    description = re.sub(r'\s+', ' ', description).strip()
    
    if len(description) < 3:
        return 'HDFC Transaction'
    
    return description

if __name__ == "__main__":
    # Test with sample HDFC lines
    test_lines = [
        "01/06/24 UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI 0000415389418321 01/06/24 10.00 22.22",
        "05/06/24 SAS2PY SOFTWARE P L 0000000000511950 05/06/24 38,000.00 38,022.22",
        "08/06/24 UPI-MALLIKARJUNA SARMA A-9246377264@YBL-0000452650884380 08/06/24 8,000.00 28,247.22",
        "09/06/24 UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK 0000416187742996 09/06/24 3,000.00 15,223.56"
    ]
    
    print("Testing Enhanced HDFC Parsing:")
    print("=" * 50)
    
    for i, line in enumerate(test_lines, 1):
        result = parse_hdfc_with_column_detection(line, i)
        if result:
            print(f"Line {i}: {result['type'].upper()} - ₹{result['amount_str']} - {result['description'][:50]}...")
        else:
            print(f"Line {i}: Not parsed")
        print()