"""
Comprehensive Bank Statement Analysis
Analyzes all PDF files to ensure accurate transaction parsing for all banks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService
import PyPDF2
import re
from datetime import datetime

def extract_and_analyze_pdf(pdf_path, bank_name):
    """Extract and analyze a PDF for transaction parsing accuracy."""
    print(f"\n{'='*80}")
    print(f"ANALYZING {bank_name.upper()} BANK STATEMENT: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract full text
            full_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                full_text += page.extract_text() + "\n"
            
            print(f"PDF Pages: {len(pdf_reader.pages)}")
            print(f"Total Text Length: {len(full_text)} characters")
            
            # Split into lines for analysis
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            print(f"Total Lines: {len(lines)}")
            
            # Initialize service
            service = TransactionImportService()
            
            # Parse based on bank type
            if bank_name.lower() == 'hdfc':
                transactions = service._parse_hdfc_transactions(lines)
            elif bank_name.lower() == 'sbi':
                transactions = service._parse_sbi_transactions(lines)
            elif bank_name.lower() == 'axis':
                transactions = service._parse_axis_transactions(lines)
            elif bank_name.lower() == 'federal' or bank_name.lower() == 'fed':
                transactions = service._parse_federal_transactions(lines)
            else:
                transactions = service._parse_hdfc_transactions(lines)
            
            print(f"\n*** PARSING RESULTS ***")
            print(f"Transactions Found: {len(transactions)}")
            
            # Analyze by date
            date_counts = {}
            transaction_types = {'income': 0, 'expense': 0}
            
            for trans in transactions:
                date_str = trans.get('date_str', 'Unknown')
                trans_type = trans.get('type', 'unknown')
                
                if date_str not in date_counts:
                    date_counts[date_str] = 0
                date_counts[date_str] += 1
                
                if trans_type in transaction_types:
                    transaction_types[trans_type] += 1
            
            print(f"\nTransaction Types:")
            print(f"  Income: {transaction_types['income']}")
            print(f"  Expense: {transaction_types['expense']}")
            
            print(f"\nTransactions by Date (showing dates with multiple transactions):")
            sorted_dates = sorted(date_counts.items(), key=lambda x: x[1], reverse=True)
            
            for date_str, count in sorted_dates:
                if count > 1:
                    print(f"  {date_str}: {count} transactions")
                    # Show details for this date
                    date_transactions = [t for t in transactions if t.get('date_str') == date_str]
                    for i, trans in enumerate(date_transactions, 1):
                        desc = trans.get('description', 'No description')[:50]
                        amount = trans.get('amount_str', '0')
                        print(f"    {i}. {desc} - ₹{amount}")
            
            # Special focus on June 27, 2024 for HDFC
            if bank_name.lower() == 'hdfc':
                print(f"\n*** JUNE 27TH DETAILED ANALYSIS ***")
                june_27_transactions = [
                    t for t in transactions 
                    if '27' in t.get('date_str', '') and '06' in t.get('date_str', '') and '2024' in t.get('date_str', '')
                ]
                
                print(f"June 27, 2024 transactions found: {len(june_27_transactions)}")
                for i, trans in enumerate(june_27_transactions, 1):
                    print(f"  {i}. {trans.get('description')} - ₹{trans.get('amount_str')} ({trans.get('type')})")
                    print(f"      Source: {trans.get('source_line')[:100]}")
                    print(f"      Pattern: {trans.get('pattern_used')}")
                
                # Also check raw text for June 27 references
                print(f"\nRAW TEXT ANALYSIS for June 27:")
                june_27_lines = []
                for i, line in enumerate(lines):
                    if '27/06/24' in line or '27/06/2024' in line:
                        june_27_lines.append((i+1, line))
                
                print(f"Lines containing '27/06/24' or '27/06/2024': {len(june_27_lines)}")
                for line_num, line in june_27_lines:
                    print(f"  Line {line_num}: {line}")
            
            # Show sample transactions
            print(f"\n*** SAMPLE TRANSACTIONS ***")
            for i, trans in enumerate(transactions[:10], 1):
                desc = trans.get('description', 'No description')[:40]
                amount = trans.get('amount_str', '0')
                date_str = trans.get('date_str', 'Unknown')
                trans_type = trans.get('type', 'unknown')
                pattern = trans.get('pattern_used', 'N/A')
                
                print(f"{i:2d}. {date_str} | {desc:40s} | ₹{amount:>10s} | {trans_type:7s} | P{pattern}")
            
            if len(transactions) > 10:
                print(f"... and {len(transactions) - 10} more transactions")
            
            return {
                'bank_name': bank_name,
                'total_transactions': len(transactions),
                'transactions': transactions,
                'date_counts': date_counts,
                'transaction_types': transaction_types,
                'pdf_pages': len(pdf_reader.pages),
                'total_lines': len(lines)
            }
            
    except Exception as e:
        print(f"❌ Error processing {bank_name} PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def find_potential_missed_transactions(lines, bank_name):
    """Look for potential transaction patterns that might be missed."""
    print(f"\n*** POTENTIAL MISSED TRANSACTIONS ANALYSIS ***")
    
    # Common transaction patterns across banks
    potential_patterns = [
        r'\d{2}/\d{2}/\d{2,4}.*?[\d,]+\.\d{2}',  # Date with amount
        r'UPI-.*?[\d,]+\.\d{2}',  # UPI transactions
        r'ATM.*?[\d,]+\.\d{2}',   # ATM transactions
        r'NEFT.*?[\d,]+\.\d{2}',  # NEFT transactions
        r'RTGS.*?[\d,]+\.\d{2}',  # RTGS transactions
        r'IMPS.*?[\d,]+\.\d{2}',  # IMPS transactions
    ]
    
    potential_transactions = []
    
    for pattern in potential_patterns:
        matches = []
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                matches.append((i+1, line))
        
        if matches:
            potential_transactions.extend(matches)
    
    # Remove duplicates
    unique_potential = list(set(potential_transactions))
    
    print(f"Found {len(unique_potential)} lines with potential transaction patterns:")
    for line_num, line in sorted(unique_potential)[:20]:  # Show first 20
        print(f"  Line {line_num}: {line[:100]}")
    
    if len(unique_potential) > 20:
        print(f"... and {len(unique_potential) - 20} more potential transaction lines")
    
    return unique_potential

def main():
    """Main analysis function."""
    print("COMPREHENSIVE BANK STATEMENT ANALYSIS")
    print("=" * 80)
    
    # PDF files to analyze
    test_data_dir = "test_data"
    pdf_files = {
        'hdfc': os.path.join(test_data_dir, 'test_hdfc.pdf'),
        'sbi': os.path.join(test_data_dir, 'test_sbi.pdf'),
        'axis': os.path.join(test_data_dir, 'test_axis.pdf'),
        'federal': os.path.join(test_data_dir, 'test_fed.pdf')
    }
    
    results = {}
    
    # Analyze each bank's PDF
    for bank_name, pdf_path in pdf_files.items():
        if os.path.exists(pdf_path):
            result = extract_and_analyze_pdf(pdf_path, bank_name)
            if result:
                results[bank_name] = result
        else:
            print(f"❌ PDF file not found: {pdf_path}")
    
    # Summary report
    print(f"\n{'='*80}")
    print("SUMMARY REPORT")
    print(f"{'='*80}")
    
    total_transactions = 0
    for bank_name, result in results.items():
        total_transactions += result['total_transactions']
        print(f"{bank_name.upper():8s}: {result['total_transactions']:3d} transactions from {result['pdf_pages']} pages ({result['total_lines']} lines)")
    
    print(f"\nTOTAL TRANSACTIONS ACROSS ALL BANKS: {total_transactions}")
    
    # Recommendations
    print(f"\n*** RECOMMENDATIONS ***")
    
    for bank_name, result in results.items():
        if bank_name == 'hdfc':
            june_27_count = len([t for t in result['transactions'] 
                               if '27' in t.get('date_str', '') and '06' in t.get('date_str', '')])
            if june_27_count < 2:
                print(f"⚠️  HDFC: Only {june_27_count} June 27th transaction found (user expects 2)")
                print(f"   → Need to investigate HDFC parsing patterns for June 27th")
        
        # Check for low transaction count relative to PDF size
        if result['total_transactions'] < result['total_lines'] / 20:  # Heuristic
            print(f"⚠️  {bank_name.upper()}: Low transaction density ({result['total_transactions']} transactions from {result['total_lines']} lines)")
            print(f"   → May be missing transactions due to parsing patterns")
    
    return results

if __name__ == "__main__":
    results = main()