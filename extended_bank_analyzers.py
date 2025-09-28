#!/usr/bin/env python3

"""
Extended Bank PDF Analyzers

Additional bank-specific analyzers for major Indian banks
"""

import re
import logging
from typing import Dict, List, Optional
from bank_pdf_analyzers import BankPDFAnalyzer

logger = logging.getLogger(__name__)

class AxisBankAnalyzer(BankPDFAnalyzer):
    """Axis Bank PDF Analyzer"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Axis Bank"
        self.column_headers = [
            "Tran Date", "Chq No", "Particulars", "Debit", "Credit", "Balance", "Init.Br"
        ]
    
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect Axis Bank statement"""
        axis_indicators = [
            'AXIS BANK LTD',
            'Axis Bank Limited',
            'Tran Date Chq No Particulars Debit Credit Balance Init.',
            'Tran Date Chq No Particulars'
        ]
        return any(indicator in pdf_text for indicator in axis_indicators)
    
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse Axis Bank transactions"""
        transactions = []
        lines = pdf_text.split('\n')
        
        # Axis Bank patterns - DD/MM/YYYY format with separate Debit/Credit columns
        axis_patterns = [
            r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\w+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
            r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$'
        ]
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if len(line) < 20:
                continue
                
            for pattern_num, pattern in enumerate(axis_patterns, 1):
                match = re.search(pattern, line)
                if match:
                    try:
                        transaction = self._parse_axis_transaction(match, pattern_num, line)
                        if transaction:
                            transactions.append(transaction)
                            break
                    except Exception as e:
                        continue
        
        return transactions
    
    def _parse_axis_transaction(self, match, pattern_num: int, full_line: str) -> Optional[Dict]:
        """Parse Axis Bank transaction"""
        try:
            date_str = match.group(1)
            description = match.group(2).strip()
            
            if pattern_num == 1:  # With reference
                debit_amt = match.group(4).replace(',', '')
                credit_amt = match.group(5).replace(',', '')
                balance = match.group(6).replace(',', '')
            else:  # Simple format
                debit_amt = match.group(3).replace(',', '')
                credit_amt = match.group(4).replace(',', '')
                balance = match.group(5).replace(',', '')
            
            # Axis Logic: Non-zero debit = expense, Non-zero credit = income
            if float(debit_amt) > 0:
                amount = float(debit_amt)
                transaction_type = 'expense'
            else:
                amount = float(credit_amt)
                transaction_type = 'income'
            
            return {
                'date': date_str,
                'description': description,
                'amount': amount,
                'type': transaction_type,
                'balance': float(balance),
                'bank': 'Axis',
                'raw_line': full_line
            }
        except Exception:
            return None
    
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """Axis Bank classification"""
        return context.get('type', 'expense')

class KotakBankAnalyzer(BankPDFAnalyzer):
    """Kotak Mahindra Bank PDF Analyzer"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Kotak Mahindra Bank"
        self.column_headers = [
            "Date", "Description", "Instrument", "Debit Amount", "Credit Amount", "Available Balance"
        ]
    
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect Kotak Bank statement"""
        kotak_indicators = [
            'KOTAK MAHINDRA BANK LIMITED',
            'Kotak Bank',
            'Date Description Instrument Debit Amount Credit Amount Available Balance'
        ]
        return any(indicator in pdf_text for indicator in kotak_indicators)
    
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse Kotak Bank transactions"""
        transactions = []
        lines = pdf_text.split('\n')
        
        # Kotak patterns
        kotak_patterns = [
            r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\w+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$'
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) < 20:
                continue
                
            for pattern in kotak_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        debit_amt = match.group(4).replace(',', '')
                        credit_amt = match.group(5).replace(',', '')
                        balance = match.group(6).replace(',', '')
                        
                        if float(debit_amt) > 0:
                            amount = float(debit_amt)
                            transaction_type = 'expense'
                        else:
                            amount = float(credit_amt)
                            transaction_type = 'income'
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'amount': amount,
                            'type': transaction_type,
                            'balance': float(balance),
                            'bank': 'Kotak',
                            'raw_line': line
                        })
                        break
                    except Exception:
                        continue
        
        return transactions
    
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """Kotak Bank classification"""
        return context.get('type', 'expense')

class FederalBankAnalyzer(BankPDFAnalyzer):
    """Federal Bank PDF Analyzer"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Federal Bank"
        self.column_headers = [
            "Date", "Value Date", "Particulars", "Tran Type", "Tran ID", "Cheque Details", "Withdrawals", "Deposits", "Balance", "DR/CR"
        ]
    
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect Federal Bank statement"""
        federal_indicators = [
            'THE FEDERAL BANK LTD',
            'Federal Bank Limited',
            'Date Value Date Particulars Tran',
            'Withdrawals Deposits Balance DR',
            'Tran Type Tran ID Cheque'
        ]
        return any(indicator in pdf_text for indicator in federal_indicators)
    
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse Federal Bank transactions"""
        transactions = []
        lines = pdf_text.split('\n')
        
        # Federal Bank patterns with complex column structure
        # Date Value Date Particulars Tran Type Tran ID Cheque Details Withdrawals Deposits Balance DR/CR
        federal_patterns = [
            r'^(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+?)\s+(\w+)\s+(\w+)\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+(DR|CR)$',
            # Simplified pattern for basic parsing
            r'^(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$'
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) < 20:
                continue
                
            for pattern in federal_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        if len(match.groups()) >= 10:  # Complex format
                            date_str = match.group(1).replace('-', '/')
                            value_date = match.group(2)
                            description = match.group(3).strip()
                            tran_type = match.group(4)
                            tran_id = match.group(5)
                            cheque_details = match.group(6)
                            withdrawal = match.group(7).replace(',', '')
                            deposit = match.group(8).replace(',', '')
                            balance = match.group(9).replace(',', '')
                            dr_cr = match.group(10)
                        else:  # Simple format
                            date_str = match.group(1).replace('-', '/')
                            description = match.group(2).strip()
                            withdrawal = match.group(3).replace(',', '')
                            deposit = match.group(4).replace(',', '')
                            balance = match.group(5).replace(',', '')
                        
                        if float(withdrawal) > 0:
                            amount = float(withdrawal)
                            transaction_type = 'expense'
                        else:
                            amount = float(deposit)
                            transaction_type = 'income'
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'amount': amount,
                            'type': transaction_type,
                            'balance': float(balance),
                            'bank': 'Federal',
                            'raw_line': line
                        })
                        break
                    except Exception:
                        continue
        
        return transactions
    
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """Federal Bank classification"""
        return context.get('type', 'expense')

class IDFCBankAnalyzer(BankPDFAnalyzer):
    """IDFC First Bank PDF Analyzer"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "IDFC First Bank"
        self.column_headers = [
            "Transaction Date", "Description", "Debit", "Credit", "Balance"
        ]
    
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect IDFC Bank statement"""
        idfc_indicators = [
            'IDFC FIRST BANK LIMITED',
            'IDFC Bank',
            'Transaction Date Description Debit Credit Balance'
        ]
        return any(indicator in pdf_text for indicator in idfc_indicators)
    
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse IDFC Bank transactions"""
        transactions = []
        lines = pdf_text.split('\n')
        
        # IDFC patterns
        idfc_patterns = [
            r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$'
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) < 20:
                continue
                
            for pattern in idfc_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        debit = match.group(3).replace(',', '')
                        credit = match.group(4).replace(',', '')
                        balance = match.group(5).replace(',', '')
                        
                        if float(debit) > 0:
                            amount = float(debit)
                            transaction_type = 'expense'
                        else:
                            amount = float(credit)
                            transaction_type = 'income'
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'amount': amount,
                            'type': transaction_type,
                            'balance': float(balance),
                            'bank': 'IDFC',
                            'raw_line': line
                        })
                        break
                    except Exception:
                        continue
        
        return transactions
    
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """IDFC Bank classification"""
        return context.get('type', 'expense')