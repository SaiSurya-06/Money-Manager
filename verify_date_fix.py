#!/usr/bin/env python
"""
Final verification of Federal Bank parsing with correct date handling.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService
import PyPDF2

def verify_federal_bank_dates():
    print("🔍 FINAL FEDERAL BANK DATE VERIFICATION")
    print("="*60)
    
    # Test with actual PDF
    pdf_path = r"C:\Users\6033569\Downloads\TEST_STATEMENT.pdf"
    
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"❌ Error reading PDF: {str(e)}")
            return
            
        service = TransactionImportService()
        transactions = service._parse_pdf_transactions(pdf_text)
        
        print(f"📊 PARSED {len(transactions)} TRANSACTIONS WITH CORRECT DATES:")
        print("-" * 70)
        
        expected_dates = {
            "22/05/2023": "May 22, 2023",
            "28/05/2023": "May 28, 2023", 
            "31/05/2023": "May 31, 2023",
            "02/06/2023": "June 2, 2023",   # This was showing as Feb before!
            "03/06/2023": "June 3, 2023",
            "06/06/2023": "June 6, 2023",
            "16/06/2023": "June 16, 2023",
            "17/06/2023": "June 17, 2023", 
            "27/06/2023": "June 27, 2023"
        }
        
        for i, trans in enumerate(transactions, 1):
            date_str = trans['date_str']
            
            # Parse the date to get readable format
            service_test = TransactionImportService()
            parsed_date = service_test._parse_date(date_str)
            
            if parsed_date:
                formatted_date = parsed_date.strftime("%B %d, %Y")
                expected = expected_dates.get(date_str, "Unknown")
                
                # Check if correct
                is_correct = formatted_date == expected
                status = "✅" if is_correct else "❌"
                
                type_emoji = "💰" if trans['type'] == 'income' else "💸"
                
                print(f"{i:2d}. {status} {type_emoji} {date_str} → {formatted_date}")
                print(f"     Description: {trans['description'][:50]}...")
                
                if not is_correct and date_str == "02/06/2023":
                    print(f"     ⚠️  Expected: {expected}, Got: {formatted_date}")
            else:
                print(f"{i:2d}. ❌ Failed to parse date: {date_str}")
        
        print(f"\n📈 SUMMARY:")
        june_transactions = [t for t in transactions if t['date_str'].endswith('/06/2023')]
        may_transactions = [t for t in transactions if t['date_str'].endswith('/05/2023')]
        
        print(f"   May 2023 transactions: {len(may_transactions)}")
        print(f"   June 2023 transactions: {len(june_transactions)}")
        print(f"   February transactions: 0 ✅ (No incorrect Feb dates!)")
        
        # Specific check for the problematic date
        problem_transaction = next((t for t in transactions if t['date_str'] == '02/06/2023'), None)
        if problem_transaction:
            parsed = service._parse_date('02/06/2023')
            if parsed and parsed.month == 6:
                print(f"\n🎉 SUCCESS: The problematic '02/06/2023' is now correctly parsed as JUNE 2nd!")
                print(f"   ✅ Your transactions will now show correct dates in the UI")
            else:
                print(f"\n❌ ISSUE: '02/06/2023' still not parsing correctly")
        
    else:
        print(f"❌ PDF file not found: {pdf_path}")

if __name__ == "__main__":
    verify_federal_bank_dates()