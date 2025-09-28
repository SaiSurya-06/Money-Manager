#!/usr/bin/env python3

"""
Analyze HDFC statement structure to understand Withdrawal vs Deposit columns

Based on server logs, the HDFC format is:
Date | Narration | Chq./Ref.No. | Value Dt | Withdrawal Amt. | Deposit Amt. | Closing Balance

Examples from logs:
01/06/24 UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI 0000415389418321 01/06/24 10.00 22.22
05/06/24 SAS2PY SOFTWARE P L 0000000000511950 05/06/24 38,000.00 38,022.22
"""

def analyze_hdfc_structure():
    """Analyze actual HDFC transaction lines from server logs"""
    
    # Real examples from the server logs
    sample_lines = [
        # Line with withdrawal amount (expense)
        "01/06/24 UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI 0000415389418321 01/06/24 10.00 22.22",
        
        # Line with deposit amount (income) 
        "05/06/24 SAS2PY SOFTWARE P L 0000000000511950 05/06/24 38,000.00 38,022.22",
        
        # More examples from logs
        "08/06/24 UPI-MALLIKARJUNA SARMA A-9246377264@YBL-0000452650884380 08/06/24 8,000.00 28,247.22",
        "09/06/24 UPI-BEHARA SRI SAI ARJUN-SAIARJUN1202@OK 0000416187742996 09/06/24 3,000.00 15,223.56"
    ]
    
    print("HDFC Statement Structure Analysis")
    print("=" * 50)
    print("Format: Date | Narration | Chq./Ref.No. | Value Dt | Withdrawal Amt. | Deposit Amt. | Closing Balance")
    print()
    
    for i, line in enumerate(sample_lines, 1):
        print(f"Sample {i}:")
        print(f"Raw: {line}")
        
        # Parse the structure manually to understand it
        parts = line.split()
        
        # Find the amounts (look for decimal patterns)
        amounts = []
        amount_positions = []
        
        for j, part in enumerate(parts):
            if '.' in part and part.replace(',', '').replace('.', '').isdigit():
                amounts.append(part)
                amount_positions.append(j)
        
        print(f"Found amounts: {amounts} at positions: {amount_positions}")
        
        # Analyze based on number of amounts
        if len(amounts) == 2:
            print(f"  Two amounts found:")
            print(f"    Amount 1: {amounts[0]} (transaction amount)")
            print(f"    Amount 2: {amounts[1]} (closing balance)")
            
            # Determine if withdrawal or deposit based on context
            line_lower = line.lower()
            if 'upi-' in line_lower and not any(term in line_lower for term in ['software', 'company', 'salary']):
                print(f"    Interpretation: UPI payment = WITHDRAWAL (expense)")
                print(f"    Column structure: Withdrawal={amounts[0]}, Deposit=empty, Balance={amounts[1]}")
            elif any(term in line_lower for term in ['software', 'salary', 'interest']):
                print(f"    Interpretation: Company payment = DEPOSIT (income)")  
                print(f"    Column structure: Withdrawal=empty, Deposit={amounts[0]}, Balance={amounts[1]}")
            else:
                print(f"    Interpretation: Need more context")
                
        elif len(amounts) == 3:
            print(f"  Three amounts found:")
            print(f"    Amount 1: {amounts[0]} (could be withdrawal)")
            print(f"    Amount 2: {amounts[1]} (could be deposit)")  
            print(f"    Amount 3: {amounts[2]} (closing balance)")
            
        print()

if __name__ == "__main__":
    analyze_hdfc_structure()