#!/usr/bin/env python
"""
PDF Diagnostic Tool for HDFC Bank Statements
This tool helps diagnose PDF extraction issues
"""
import os
import sys
import logging
import PyPDF2
from io import StringIO

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')

import django
django.setup()

def diagnose_pdf(file_path):
    """Diagnose PDF extraction issues."""
    print("🔍 PDF DIAGNOSTIC TOOL")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📄 Analyzing: {file_path}")
    print(f"📏 File size: {os.path.getsize(file_path)} bytes")
    
    try:
        with open(file_path, 'rb') as file:
            # Basic PDF info
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"📑 Total pages: {len(pdf_reader.pages)}")
            print(f"🔒 Encrypted: {pdf_reader.is_encrypted}")
            
            if pdf_reader.metadata:
                print("📝 PDF Metadata:")
                for key, value in pdf_reader.metadata.items():
                    print(f"   {key}: {value}")
            
            # Test text extraction
            print("\n🔤 Text Extraction Test:")
            print("-" * 40)
            
            total_text = ""
            for page_num in range(min(3, len(pdf_reader.pages))):  # Test first 3 pages
                try:
                    page = pdf_reader.pages[page_num]
                    
                    # Method 1: Standard extraction
                    text1 = page.extract_text()
                    
                    # Method 2: Alternative extraction
                    text2 = ""
                    try:
                        if hasattr(page, 'extractText'):
                            text2 = page.extractText()
                    except:
                        pass
                    
                    print(f"Page {page_num + 1}:")
                    print(f"  Standard method: {len(text1)} characters")
                    print(f"  Alternative method: {len(text2)} characters")
                    
                    # Use the better extraction
                    page_text = text1 if len(text1) >= len(text2) else text2
                    
                    if page_text:
                        total_text += page_text + "\n"
                        # Show first few lines
                        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                        print(f"  First few lines:")
                        for i, line in enumerate(lines[:3]):
                            print(f"    {i+1}. {line[:60]}...")
                    else:
                        print(f"  ❌ No text extracted")
                        
                        # Check if page has content
                        if hasattr(page, 'get_contents'):
                            print(f"  Page has content objects: Yes")
                        else:
                            print(f"  Page has content objects: Unknown")
                    
                    print()
                    
                except Exception as e:
                    print(f"  ❌ Error on page {page_num + 1}: {e}")
            
            # Overall assessment
            print("📊 DIAGNOSTIC SUMMARY:")
            print("=" * 40)
            
            if total_text.strip():
                print("✅ PDF text extraction: SUCCESS")
                print(f"📏 Total extracted text: {len(total_text)} characters")
                
                # Check for bank-related content
                bank_keywords = ['hdfc', 'bank', 'statement', 'account', 'transaction', 'balance']
                found_keywords = [kw for kw in bank_keywords if kw.lower() in total_text.lower()]
                
                if found_keywords:
                    print(f"🏦 Bank content detected: {', '.join(found_keywords)}")
                    print("✅ This PDF should work with the Money Manager")
                else:
                    print("⚠️  No bank-related content detected")
                
                # Check for transaction patterns
                lines_with_dates = [line for line in total_text.split('\n') 
                                  if any(char.isdigit() for char in line) and '/' in line]
                
                print(f"📅 Lines with date patterns: {len(lines_with_dates)}")
                
                if lines_with_dates:
                    print("🔍 Sample transaction-like lines:")
                    for line in lines_with_dates[:3]:
                        print(f"   {line.strip()[:80]}...")
                
            else:
                print("❌ PDF text extraction: FAILED")
                print("🔍 Possible issues:")
                print("   • PDF is image-based or scanned")
                print("   • PDF is corrupted or damaged")
                print("   • PDF uses unsupported encoding")
                print("   • PDF contains only graphics/images")
                
                print("\n💡 Recommended solutions:")
                print("   1. Re-download PDF from HDFC NetBanking")
                print("   2. Ensure 'Text Format' is selected during download")
                print("   3. Try downloading from different date range")
                print("   4. Use CSV format as alternative")
    
    except Exception as e:
        print(f"❌ Critical error analyzing PDF: {e}")

def main():
    print("🧪 PDF DIAGNOSTIC TOOL FOR HDFC STATEMENTS")
    print("=" * 60)
    
    # You can specify a PDF file path here for testing
    test_pdf_path = input("Enter PDF file path (or press Enter to skip): ").strip()
    
    if test_pdf_path and os.path.exists(test_pdf_path):
        diagnose_pdf(test_pdf_path)
    else:
        print("ℹ️  To use this tool:")
        print("   1. Place your HDFC PDF statement in this directory")
        print("   2. Run: python pdf_diagnostic.py")
        print("   3. Enter the file path when prompted")
        print("\n🔧 This tool will help identify PDF extraction issues")

if __name__ == "__main__":
    main()