#!/usr/bin/env python
"""
Script to extract and analyze the test bank statement PDF format.
"""
import os
import sys
import django
import PyPDF2
import logging

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_pdf_content(pdf_path):
    """Extract text content from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"PDF has {len(pdf_reader.pages)} pages")
            
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                print(f"\n=== PAGE {page_num} ===")
                print(page_text)
                print("=" * 50)
                full_text += page_text + "\n"
            
            return full_text
            
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return None

def analyze_statement_format(text):
    """Analyze the bank statement format and identify patterns."""
    if not text:
        return
        
    lines = text.split('\n')
    
    print(f"\n=== ANALYZING STATEMENT FORMAT ===")
    print(f"Total lines: {len(lines)}")
    
    # Look for transaction patterns
    transaction_lines = []
    date_patterns = []
    amount_patterns = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if len(line) < 10:
            continue
            
        # Check for amounts (numbers with decimal)
        if any(char.isdigit() for char in line) and ('.' in line or ',' in line):
            # Look for common transaction indicators
            if any(indicator in line.lower() for indicator in ['cr', 'dr', 'debit', 'credit']):
                transaction_lines.append((line_num, line))
                print(f"TRANSACTION LINE {line_num}: {line}")
        
        # Look for date patterns
        import re
        date_match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', line)
        if date_match:
            date_patterns.append((line_num, date_match.group(1), line))
            
        # Look for amount patterns  
        amount_match = re.search(r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b', line)
        if amount_match:
            amount_patterns.append((line_num, amount_match.group(1), line))
    
    print(f"\n=== FOUND PATTERNS ===")
    print(f"Potential transaction lines: {len(transaction_lines)}")
    print(f"Date patterns found: {len(date_patterns)}")
    print(f"Amount patterns found: {len(amount_patterns)}")
    
    if date_patterns:
        print(f"\nDATE PATTERNS:")
        for line_num, date, line in date_patterns[:5]:  # Show first 5
            print(f"  Line {line_num}: {date} -> {line[:60]}...")
    
    if transaction_lines:
        print(f"\nTRANSACTION LINES:")
        for line_num, line in transaction_lines[:10]:  # Show first 10
            print(f"  Line {line_num}: {line}")
    
    return transaction_lines, date_patterns, amount_patterns

if __name__ == "__main__":
    pdf_path = r"C:\Users\6033569\Downloads\TEST_STATEMENT.pdf"
    
    if os.path.exists(pdf_path):
        print(f"Reading PDF: {pdf_path}")
        text_content = extract_pdf_content(pdf_path)
        
        if text_content:
            print(f"\n=== RAW TEXT CONTENT ===")
            print(text_content[:2000] + "..." if len(text_content) > 2000 else text_content)
            
            # Analyze the format
            analyze_statement_format(text_content)
            
            # Save extracted text for reference
            with open("extracted_statement_text.txt", "w", encoding="utf-8") as f:
                f.write(text_content)
            print(f"\nExtracted text saved to: extracted_statement_text.txt")
        else:
            print("Failed to extract text from PDF")
    else:
        print(f"PDF file not found: {pdf_path}")