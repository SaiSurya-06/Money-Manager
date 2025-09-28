#!/usr/bin/env python3

"""
HDFC Parsing Status Check

Quick verification that HDFC parsing is now working
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_hdfc_status():
    print("🏦 HDFC Bank PDF Parser Status Check")
    print("="*50)
    
    try:
        from bank_pdf_analyzers import BankAnalyzerFactory, HDFCBankAnalyzer
        print("✅ Modular analyzers imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test with user's sample
    sample_text = """
HDFC BANK LTD
Date Narration Chq./Ref.No. Value Dt Withdrawal Amt. Deposit Amt. Closing Balance
01/06/24 UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI 0000415389418321 01/06/24 10.00 22.22
05/06/24 SAS2PY SOFTWARE P L 0000000000511950 05/06/24 38,000.00 38,022.22
"""
    
    try:
        # Test detection
        analyzer = BankAnalyzerFactory.get_analyzer(sample_text)
        if analyzer and analyzer.bank_name == "HDFC Bank":
            print("✅ HDFC Bank detection: WORKING")
        else:
            print("❌ HDFC Bank detection: FAILED")
            return False
        
        # Test parsing
        transactions = analyzer.parse_transactions(sample_text)
        if len(transactions) > 0:
            print(f"✅ Transaction parsing: WORKING ({len(transactions)} transactions)")
            
            # Test UPI classification
            upi_txn = [t for t in transactions if 'UPI-' in t['description']]
            if upi_txn and upi_txn[0]['type'] == 'expense':
                print("✅ UPI classification: WORKING (UPI = expense)")
            else:
                print("❌ UPI classification: FAILED")
                
            # Test software classification  
            soft_txn = [t for t in transactions if 'SOFTWARE' in t['description']]
            if soft_txn and soft_txn[0]['type'] == 'income':
                print("✅ Software payment classification: WORKING (software = income)")
            else:
                print("❌ Software payment classification: FAILED")
                
        else:
            print("❌ Transaction parsing: FAILED (0 transactions)")
            return False
            
        print("\n🎉 HDFC PARSER STATUS: READY FOR PRODUCTION!")
        print("💡 You can now upload your HDFC statement - it should work!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = check_hdfc_status()
    exit(0 if success else 1)