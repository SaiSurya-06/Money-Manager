import PyPDF2
import sys
import re

pdf_path = r'C:\Surya Automation\SURYA - Money Manager\media\documents\sample_statement.pdf'

try:
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        all_text = ''
        for page in pdf.pages:
            all_text += page.extract_text() + '\n'
    
    # Split into lines and find June 27 transactions
    lines = all_text.split('\n')
    june_27_lines = []
    
    print('=== SEARCHING FOR JUNE 27, 2024 TRANSACTIONS ===')
    for i, line in enumerate(lines):
        line = line.strip()
        if '27/06/24' in line or '27/06/2024' in line:
            # Print context around the line
            start = max(0, i-2)
            end = min(len(lines), i+3)
            print(f'\n--- Context around line {i+1} ---')
            for j in range(start, end):
                prefix = '>>> ' if j == i else '    '
                print(f'{prefix}Line {j+1}: {lines[j]}')
            june_27_lines.append(line)
    
    print(f'\n=== SUMMARY ===')
    print(f'Total lines with 27/06/24 or 27/06/2024: {len(june_27_lines)}')
    for i, line in enumerate(june_27_lines, 1):
        print(f'Transaction {i}: {line}')
        
    # Also search for patterns that might span multiple lines
    print(f'\n=== SEARCHING FOR MULTI-LINE TRANSACTIONS AROUND JUNE 27 ===')
    content_block = ""
    for i, line in enumerate(lines):
        line = line.strip()
        if '27/06/24' in line or '27/06/2024' in line or 'BEHARA' in line or 'UPI-' in line:
            # Show a 5-line window
            start = max(0, i-2)  
            end = min(len(lines), i+4)
            print(f'\n--- Multi-line context around line {i+1} ---')
            for j in range(start, end):
                marker = '>>>' if j == i else '   '
                print(f'{marker}Line {j+1}: "{lines[j].strip()}"')
                
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()