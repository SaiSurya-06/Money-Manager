#!/usr/bin/env python
"""
Analyze actual PDF files to understand bank detection issues and improve parsing.
"""
import os
import sys
import django
import PyPDF2
from datetime import datetime
import logging
import re

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService

def analyze_pdf_content(pdf_path, expected_bank):
    """Analyze PDF content to understand structure and identify parsing issues."""
    
    print(f"\n{'='*80}")
    print(f"ANALYZING: {os.path.basename(pdf_path)} (Expected: {expected_bank})")
    print(f"{'='*80}")
    
    try:
        # Extract PDF text
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() + "\n"
        
        print(f"✅ Successfully extracted PDF text ({len(pdf_text)} characters)")
        
        # Initialize service
        service = TransactionImportService()
        
        # Show first 1000 characters for analysis
        print(f"\n📄 PDF Content Preview (first 1000 chars):")
        print("-" * 60)
        print(pdf_text[:1000])
        print("-" * 60)
        
        # Test bank detection with current logic
        detected_bank = service._detect_bank_type(pdf_text)
        print(f"\n🏦 Bank Detection:")
        print(f"   Expected: {expected_bank}")
        print(f"   Detected: {detected_bank}")
        print(f"   Status: {'✅ CORRECT' if detected_bank == expected_bank else '❌ INCORRECT'}")
        
        # Check for bank identifiers
        text_lower = pdf_text.lower()
        
        print(f"\n🔍 Bank Identifier Analysis:")
        
        # Check for various bank identifiers
        bank_indicators = {
            'SBI': ['state bank of india', 'sbi', 'sbin0', 'state bank'],
            'HDFC': ['hdfc bank', 'housing development finance', 'hdfc0', 'hdfc'],
            'AXIS': ['axis bank', 'axis bank limited', 'utib', 'utib0'],
            'FEDERAL': ['federal bank', 'federal towers', 'fdrl', 'fdrlinbb'],
            'ICICI': ['icici bank', 'icici', 'icic0'],
            'KOTAK': ['kotak mahindra bank', 'kotak', 'kkbk0'],
        }
        
        found_indicators = {}
        for bank, indicators in bank_indicators.items():
            found = [indicator for indicator in indicators if indicator in text_lower]
            if found:
                found_indicators[bank] = found
        
        if found_indicators:
            for bank, indicators in found_indicators.items():
                print(f"   🏦 {bank}: {indicators}")
        else:
            print(f"   ❌ No known bank indicators found")
        
        # Analyze transaction patterns
        print(f"\n📊 Transaction Pattern Analysis:")
        lines = pdf_text.split('\n')
        
        # Look for common transaction line patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # DD/MM/YY or DD-MM-YYYY
            r'\d{2}-[A-Z]{3}-\d{2,4}',          # DD-MMM-YYYY
            r'\d{4}-\d{2}-\d{2}'               # YYYY-MM-DD
        ]
        
        amount_patterns = [
            r'\d+[,\d]*\.\d{2}',               # Decimal amounts
            r'[\d,]+\.\d{2}'                   # Currency amounts
        ]
        
        transaction_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 20:  # Skip short lines
                continue
                
            has_date = any(re.search(pattern, line) for pattern in date_patterns)
            has_amount = any(re.search(pattern, line) for pattern in amount_patterns)
            
            if has_date and has_amount:
                transaction_lines.append((i+1, line))
        
        print(f"   Found {len(transaction_lines)} potential transaction lines")
        
        # Show first few transaction lines
        if transaction_lines:
            print(f"\n📝 Sample Transaction Lines:")
            for line_num, line in transaction_lines[:5]:
                print(f"   Line {line_num}: {line[:100]}...")
        
        # Try parsing with current implementation
        print(f"\n🔧 Current Parsing Results:")
        transactions = service._parse_pdf_transactions(pdf_text)
        print(f"   Transactions Found: {len(transactions)}")
        
        if transactions:
            income_count = sum(1 for t in transactions if t['type'] == 'income')
            expense_count = sum(1 for t in transactions if t['type'] == 'expense')
            print(f"   Income: {income_count}, Expense: {expense_count}")
            
            print(f"\n   Sample Parsed Transactions:")
            for i, trans in enumerate(transactions[:3], 1):
                print(f"     {i}. {trans.get('date_str', 'N/A')} | ₹{trans.get('amount_str', '0')} | {trans.get('type', 'unknown')} | {trans.get('description', 'N/A')[:50]}...")
        
        # Provide recommendations
        print(f"\n💡 Recommendations:")
        
        if detected_bank != expected_bank:
            if expected_bank in found_indicators:
                print(f"   🔧 Add stronger {expected_bank} indicators: {found_indicators[expected_bank]}")
            else:
                print(f"   🔍 Need to identify {expected_bank} specific text patterns")
        
        if len(transactions) == 0:
            print(f"   📝 Create specific parsing patterns for this {expected_bank} format")
            if transaction_lines:
                print(f"   📊 Use the {len(transaction_lines)} identified transaction lines as reference")
        
        return {
            'bank_detected_correctly': detected_bank == expected_bank,
            'transactions_found': len(transactions),
            'potential_transaction_lines': len(transaction_lines),
            'found_indicators': found_indicators
        }
        
    except Exception as e:
        print(f"❌ Error analyzing PDF: {str(e)}")
        return None

def main():
    """Analyze all available PDF files."""
    
    print("🔍 PDF CONTENT ANALYSIS FOR BANK DETECTION IMPROVEMENT")
    print("=" * 80)
    
    # PDF files to analyze
    pdf_files = [
        (r"C:\Users\6033569\Downloads\test_sbi.pdf", "SBI"),
        (r"C:\Users\6033569\Downloads\test_hdfc.pdf", "HDFC"), 
        (r"C:\Users\6033569\Downloads\test_axis.pdf", "AXIS")
    ]
    
    results = {}
    
    for pdf_path, expected_bank in pdf_files:
        if os.path.exists(pdf_path):
            result = analyze_pdf_content(pdf_path, expected_bank)
            if result:
                results[expected_bank] = result
        else:
            print(f"\n⚠️  {expected_bank} PDF not found: {pdf_path}")
    
    # Summary
    if results:
        print(f"\n{'='*80}")
        print(f"ANALYSIS SUMMARY")
        print(f"{'='*80}")
        
        print(f"\n📊 Results Summary:")
        
        for bank, result in results.items():
            detection_status = "✅" if result['bank_detected_correctly'] else "❌"
            parsing_status = "✅" if result['transactions_found'] > 0 else "❌"
            
            print(f"   {bank}:")
            print(f"     {detection_status} Bank Detection")
            print(f"     {parsing_status} Transaction Parsing ({result['transactions_found']} transactions)")
            print(f"     📝 Potential Lines: {result['potential_transaction_lines']}")
        
        # Overall recommendations
        print(f"\n🎯 Overall Recommendations:")
        
        failed_detections = [bank for bank, result in results.items() if not result['bank_detected_correctly']]
        if failed_detections:
            print(f"   1. Fix bank detection for: {', '.join(failed_detections)}")
        
        failed_parsing = [bank for bank, result in results.items() if result['transactions_found'] == 0]
        if failed_parsing:
            print(f"   2. Implement parsing patterns for: {', '.join(failed_parsing)}")
        
        successful_banks = [bank for bank, result in results.items() 
                          if result['bank_detected_correctly'] and result['transactions_found'] > 0]
        if successful_banks:
            print(f"   3. Successfully implemented: {', '.join(successful_banks)}")
    
    else:
        print(f"\n⚠️  No PDF files were successfully analyzed")
        print(f"   Make sure PDF files are available in the expected locations")

if __name__ == "__main__":
    main()