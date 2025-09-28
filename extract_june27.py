"""
Quick investigation of the June 27th issue - let's extract the actual PDF content around June 27th
"""

import PyPDF2
import re

def extract_pdf_around_june_27():
    """Extract raw text around June 27 to find the missing transaction."""
    try:
        # Find PDF files in the workspace
        import os
        pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
        
        if not pdf_files:
            print("No PDF files found in current directory")
            return
        
        print(f"Found PDF files: {pdf_files}")
        
        # Try to process the first PDF
        pdf_file = pdf_files[0]
        print(f"\nProcessing: {pdf_file}")
        
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            full_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                full_text += page.extract_text()
            
            # Split into lines and find June 27 context
            lines = full_text.split('\n')
            june_27_lines = []
            
            for i, line in enumerate(lines):
                if '27/06/24' in line or '27/06/2024' in line:
                    # Get context: 3 lines before and after
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    
                    context = {
                        'line_number': i,
                        'line': line,
                        'context': lines[start:end]
                    }
                    june_27_lines.append(context)
            
            print(f"\n=== JUNE 27 LINES FOUND IN PDF ===")
            for entry in june_27_lines:
                print(f"\nLine {entry['line_number']}: {entry['line']}")
                print("Context:")
                for j, context_line in enumerate(entry['context']):
                    marker = " >>> " if context_line == entry['line'] else "     "
                    print(f"{marker}{context_line[:100]}")
            
            print(f"\nTotal June 27 references found: {len(june_27_lines)}")
            
            # Now let's check for transaction patterns around these lines
            print(f"\n=== TRANSACTION PATTERN ANALYSIS ===")
            transaction_patterns = [
                r'\d{2}/\d{2}/\d{2,4}\s+.*?\s+[\d,]+\.\d{2}',  # Basic transaction pattern
                r'27/06/24.*?[\d,]+\.\d{2}',  # June 27 specific
                r'UPI-.*?27/06/24',  # UPI transactions
                r'ATM.*?27/06/24'   # ATM transactions
            ]
            
            for pattern in transaction_patterns:
                matches = re.findall(pattern, full_text, re.MULTILINE | re.IGNORECASE)
                if matches:
                    print(f"\nPattern '{pattern}' found {len(matches)} matches:")
                    for match in matches:
                        print(f"  - {match[:150]}")
            
    except Exception as e:
        print(f"Error processing PDF: {e}")

if __name__ == "__main__":
    extract_pdf_around_june_27()