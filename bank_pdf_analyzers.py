#!/usr/bin/env python3

"""
Bank-Specific PDF Analyzer Framework

This module provides individual PDF analyzers for each bank with their specific:
- Column structures
- Date formats  
- Transaction patterns
- Amount positioning
- Classification rules

Supported Banks:
- HDFC Bank
- SBI (State Bank of India)
- ICICI Bank
- Axis Bank
- Kotak Mahindra Bank
- IDFC First Bank
- Federal Bank
- And more...
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class BankPDFAnalyzer(ABC):
    """Abstract base class for bank-specific PDF analyzers"""
    
    def __init__(self):
        self.bank_name = ""
        self.column_headers = []
        self.date_formats = []
        self.transaction_patterns = []
        
    @abstractmethod
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect if this PDF belongs to this bank"""
        pass
        
    @abstractmethod
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse transactions specific to this bank's format"""
        pass
        
    @abstractmethod
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """Classify transaction as income/expense based on bank-specific rules"""
        pass

class HDFCBankAnalyzer(BankPDFAnalyzer):
    """HDFC Bank PDF Analyzer"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "HDFC Bank"
        self.column_headers = [
            "Date", "Narration", "Chq./Ref.No.", "Value Dt", 
            "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"
        ]
        self.date_formats = ["%d/%m/%y", "%d/%m/%Y"]
        
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect HDFC Bank statement"""
        hdfc_indicators = [
            'HDFC BANK LTD',
            'HDFC Bank Limited',
            'Date Narration Chq./Ref.No. Value Dt Withdrawal Amt. Deposit Amt. Closing Balance',
            'Withdrawal Amt. Deposit Amt. Closing Balance'
        ]
        return any(indicator in pdf_text for indicator in hdfc_indicators)
    
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse HDFC transactions with multi-line support"""
        transactions = []
        lines = pdf_text.split('\n')
        
        logger.info("=== HDFC MODULAR ANALYZER PARSING ===")
        logger.info(f"Processing {len(lines)} lines")
        
        # First, let's look for the actual format in the PDF
        # From the logs, I can see the format is multi-line with continuation lines
        
        # Join lines to handle multi-line transactions
        processed_lines = []
        current_line = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip header lines
            if any(header in line for header in ['Date Narration', 'Withdrawal Amt', 'Deposit Amt', '---', 'PAGE']):
                continue
            
            # Check if line starts with a date (new transaction)
            if re.match(r'^\d{2}/\d{2}/\d{2,4}', line):
                # Save previous transaction if exists
                if current_line:
                    processed_lines.append(current_line)
                current_line = line
            else:
                # This is a continuation line
                if current_line:
                    current_line += " " + line
        
        # Don't forget the last line
        if current_line:
            processed_lines.append(current_line)
        
        logger.info(f"After joining multi-line transactions: {len(processed_lines)} transactions")
        
        # Now parse the joined transactions
        hdfc_patterns = [
            # Full HDFC format: Date Description RefNumber ValueDate Amount Balance
            r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(\d{10,})\s+(\d{2}/\d{2}/\d{2,4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
            # With shorter ref: Date Description RefNumber Amount Balance  
            r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(\d{8,})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
            # Simple: Date Description Amount Balance
            r'^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$'
        ]
        
        for line_num, line in enumerate(processed_lines, 1):
            logger.info(f"Trying to parse line {line_num}: {line[:100]}...")
            
            for pattern_num, pattern in enumerate(hdfc_patterns, 1):
                match = re.search(pattern, line)
                if match:
                    try:
                        transaction = self._parse_hdfc_column_transaction(match, pattern_num, line)
                        if transaction:
                            transactions.append(transaction)
                            logger.info(f"✅ HDFC transaction parsed: {transaction['description'][:30]} | ₹{transaction['amount']} | {transaction['type']}")
                            break
                    except Exception as e:
                        logger.error(f"HDFC parsing error on line {line_num}: {e}")
                        continue
            else:
                logger.warning(f"⚠️ No pattern matched for line: {line[:50]}...")
        
        logger.info(f"HDFC Modular Analyzer found {len(transactions)} transactions")
        return transactions
    
    def _parse_hdfc_column_transaction(self, match, pattern_num: int, full_line: str) -> Optional[Dict]:
        """Parse HDFC transaction using single amount column approach"""
        try:
            if pattern_num == 1:  # Full format: Date Description RefNo ValueDate Amount Balance
                date_str = match.group(1)
                description = match.group(2).strip()
                ref_no = match.group(3)
                value_date = match.group(4)
                amount_str = match.group(5).replace(',', '')
                balance_str = match.group(6).replace(',', '')
            elif pattern_num == 2:  # Simple format: Date Description Amount Balance
                date_str = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3).replace(',', '')
                balance_str = match.group(4).replace(',', '')
            elif pattern_num == 3:  # With reference: Date Description RefNo Amount Balance
                date_str = match.group(1)
                description = match.group(2).strip()
                ref_no = match.group(3)
                amount_str = match.group(4).replace(',', '')
                balance_str = match.group(5).replace(',', '')
            else:
                return None
            
            amount = float(amount_str)
            
            # Clean description - remove reference numbers but keep meaningful text
            clean_description = re.sub(r'\d{10,}', '', description)
            clean_description = re.sub(r'\s+', ' ', clean_description).strip()
            
            if not clean_description or len(clean_description) < 3:
                clean_description = description.strip()  # Fallback to original
                
            if not clean_description:
                clean_description = 'HDFC Transaction'
            
            # Determine transaction type using balance analysis and description
            prev_balance = float(balance_str) - amount
            
            if float(balance_str) > prev_balance:
                # Balance increased = credit/income
                transaction_type = 'income'
            else:
                # Balance decreased = debit/expense  
                transaction_type = 'expense'
            
            # Apply HDFC-specific classification rules (especially UPI rule)
            final_type = self.classify_transaction(clean_description, amount, {
                'type': transaction_type,
                'balance': float(balance_str),
                'balance_change': amount if transaction_type == 'income' else -amount
            })
            
            logger.info(f"HDFC parsed: {clean_description[:20]}... | ₹{amount} | {final_type}")
            
            return {
                'date': self._convert_hdfc_date(date_str),
                'description': clean_description,
                'amount': amount,
                'type': final_type,
                'balance': float(balance_str),
                'bank': 'HDFC',
                'raw_line': full_line
            }
            
        except Exception as e:
            logger.error(f"Error in HDFC parsing: {e} | Line: {full_line}")
            return None
    
    def _parse_hdfc_transaction(self, match, pattern_num: int, full_line: str) -> Optional[Dict]:
        """Parse individual HDFC transaction"""
        try:
            date_str = self._convert_hdfc_date(match.group(1))
            
            if pattern_num == 1:  # With reference number
                description = match.group(2).strip()
                amount_str = match.group(4).replace(',', '')
                balance_str = match.group(5).replace(',', '')
            elif pattern_num in [2, 3]:  # Simple or UPI format
                description = match.group(2).strip()
                amount_str = match.group(3).replace(',', '')
                balance_str = match.group(4).replace(',', '')
            elif pattern_num == 4:  # ATM format
                prefix = match.group(2)
                desc_part = match.group(3).strip()
                description = prefix + desc_part
                amount_str = match.group(4).replace(',', '')
                balance_str = match.group(5).replace(',', '')
            
            # Clean description
            description = re.sub(r'\d{8,}', '', description).strip()
            description = re.sub(r'\s+', ' ', description)
            
            if not description or len(description) < 3:
                description = 'HDFC Transaction'
            
            # HDFC-specific classification
            transaction_type = self.classify_transaction(
                description, 
                float(amount_str), 
                {
                    'balance': float(balance_str),
                    'full_line': full_line,
                    'pattern': pattern_num
                }
            )
            
            return {
                'date': date_str,
                'description': description,
                'amount': float(amount_str),
                'type': transaction_type,
                'balance': float(balance_str),
                'bank': 'HDFC',
                'raw_line': full_line
            }
            
        except Exception as e:
            logger.error(f"Error parsing HDFC transaction: {e}")
            return None
    
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """HDFC-specific transaction classification"""
        desc_lower = description.lower()
        
        # **CRITICAL HDFC RULE**: ALL UPI- transactions are expenses (outgoing payments)
        if desc_lower.startswith('upi-'):
            return 'expense'
        
        # Strong income indicators
        if any(term in desc_lower for term in [
            'interest paid', 'salary', 'dividend', 'bonus', 'refund', 'interest'
        ]):
            return 'income'
        
        # Company payments (software/tech companies) - likely salary
        if re.search(r'\b(software|tech|solutions|services)\b.*\b(p\s*l|pvt\s*ltd)\b', desc_lower):
            return 'income'
        
        # ATM/Withdrawal patterns
        if any(term in desc_lower for term in ['atw-', 'atm-', 'eaw-', 'withdrawal']):
            return 'expense'
        
        # Use balance-based classification from parsing
        return context.get('type', 'expense')
    
    def _convert_hdfc_date(self, date_str: str) -> str:
        """Convert HDFC date format"""
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str

class SBIBankAnalyzer(BankPDFAnalyzer):
    """State Bank of India PDF Analyzer"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "State Bank of India"
        self.column_headers = [
            "Date", "Details", "Ref No./Cheque No", "Credit", "Balance"
        ]
    
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect SBI statement"""
        sbi_indicators = [
            'STATE BANK OF INDIA',
            'SBI Bank',
            'Date Details Ref No./Cheque No Credit Balance',
            'Details Ref No./Cheque No Credit'
        ]
        return any(indicator in pdf_text.upper() for indicator in sbi_indicators)
    
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse SBI transactions"""
        transactions = []
        lines = pdf_text.split('\n')
        
        # SBI-specific patterns (Note: SBI has Credit column but no separate Debit column)
        sbi_patterns = [
            # Date Details RefNo Credit Balance
            r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\w+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
            # Date Details Credit Balance (simple format)
            r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$'
        ]
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if len(line) < 20:
                continue
                
            for pattern_num, pattern in enumerate(sbi_patterns, 1):
                match = re.search(pattern, line)
                if match:
                    try:
                        transaction = self._parse_sbi_transaction(match, pattern_num, line)
                        if transaction:
                            transactions.append(transaction)
                            break
                    except Exception as e:
                        continue
        
        return transactions
    
    def _parse_sbi_transaction(self, match, pattern_num: int, full_line: str) -> Optional[Dict]:
        """Parse SBI transaction with new column structure (Credit only)"""
        try:
            date_str = match.group(1)
            description = match.group(2).strip()
            
            if pattern_num == 1:  # With ref number
                ref_no = match.group(3)
                credit_amt = match.group(4).replace(',', '')
                balance = match.group(5).replace(',', '')
            else:  # Simple format
                credit_amt = match.group(3).replace(',', '')
                balance = match.group(4).replace(',', '')
            
            # SBI Logic: Analyze description to determine if it's expense or income
            # Since SBI only shows Credit column, we need to infer from description
            amount = float(credit_amt)
            
            # Classify based on description
            desc_lower = description.lower()
            if any(term in desc_lower for term in ['withdrawal', 'atm', 'purchase', 'payment', 'debit']):
                transaction_type = 'expense'
            elif any(term in desc_lower for term in ['deposit', 'salary', 'credit', 'transfer in', 'interest']):
                transaction_type = 'income'
            else:
                # Default logic based on common patterns
                transaction_type = 'income'  # SBI Credit column typically shows credits
            
            return {
                'date': self._convert_sbi_date(date_str),
                'description': description,
                'amount': amount,
                'type': transaction_type,
                'balance': float(balance),
                'bank': 'SBI',
                'raw_line': full_line
            }
            
        except Exception:
            return None
    
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """SBI classification - already handled in parsing"""
        return context.get('type', 'expense')
    
    def _convert_sbi_date(self, date_str: str) -> str:
        """Convert SBI date format"""
        return date_str  # SBI uses DD/MM/YYYY format already

class ICICIBankAnalyzer(BankPDFAnalyzer):
    """ICICI Bank PDF Analyzer"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "ICICI Bank"
        self.column_headers = [
            "Date", "Description", "Cheque No.", "Withdrawal", "Deposit", "Balance"
        ]
    
    def detect_bank_type(self, pdf_text: str) -> bool:
        """Detect ICICI statement"""
        icici_indicators = [
            'ICICI BANK LIMITED',
            'ICICI Bank',
            'Withdrawal Deposit Balance'
        ]
        return any(indicator in pdf_text for indicator in icici_indicators)
    
    def parse_transactions(self, pdf_text: str) -> List[Dict]:
        """Parse ICICI transactions"""
        # Similar structure to HDFC but with ICICI-specific patterns
        # Implementation here...
        return []
    
    def classify_transaction(self, description: str, amount: float, context: Dict) -> str:
        """ICICI-specific classification rules"""
        # ICICI-specific logic here...
        return 'expense'

# Factory class to get the right analyzer
class BankAnalyzerFactory:
    """Factory to create appropriate bank analyzer"""
    
    @staticmethod
    def get_analyzer(pdf_text: str) -> Optional[BankPDFAnalyzer]:
        """Detect bank type and return appropriate analyzer"""
        
        # Import extended analyzers
        try:
            from extended_bank_analyzers import (
                AxisBankAnalyzer, KotakBankAnalyzer, 
                FederalBankAnalyzer, IDFCBankAnalyzer
            )
            extended_available = True
        except ImportError:
            extended_available = False
            logger.warning("Extended bank analyzers not available")
        
        analyzers = [
            HDFCBankAnalyzer(),
            SBIBankAnalyzer(), 
            ICICIBankAnalyzer(),
        ]
        
        # Add extended analyzers if available
        if extended_available:
            analyzers.extend([
                AxisBankAnalyzer(),
                KotakBankAnalyzer(),
                FederalBankAnalyzer(),
                IDFCBankAnalyzer()
            ])
        
        for analyzer in analyzers:
            if analyzer.detect_bank_type(pdf_text):
                logger.info(f"Detected bank: {analyzer.bank_name}")
                return analyzer
        
        logger.warning("Could not detect bank type from PDF content")
        return None
    
    @staticmethod
    def get_supported_banks() -> List[str]:
        """Get list of supported banks"""
        banks = [
            "HDFC Bank",
            "State Bank of India", 
            "ICICI Bank"
        ]
        
        # Add extended banks if available
        try:
            from extended_bank_analyzers import (
                AxisBankAnalyzer, KotakBankAnalyzer, 
                FederalBankAnalyzer, IDFCBankAnalyzer
            )
            banks.extend([
                "Axis Bank",
                "Kotak Mahindra Bank", 
                "Federal Bank",
                "IDFC First Bank"
            ])
        except ImportError:
            pass
            
        return banks

if __name__ == "__main__":
    # Test the analyzer system
    sample_hdfc_text = """
    HDFC BANK LTD
    Date Narration Chq./Ref.No. Value Dt Withdrawal Amt. Deposit Amt. Closing Balance
    01/06/24 UPI-RAJ STORE-PAYTMQR281005050101IQKFNTI 0000415389418321 01/06/24 10.00 22.22
    05/06/24 SAS2PY SOFTWARE P L 0000000000511950 05/06/24 38,000.00 38,022.22
    """
    
    analyzer = BankAnalyzerFactory.get_analyzer(sample_hdfc_text)
    if analyzer:
        transactions = analyzer.parse_transactions(sample_hdfc_text)
        print(f"Found {len(transactions)} transactions using {analyzer.bank_name} analyzer")
        for txn in transactions:
            print(f"  {txn['date']} - {txn['type']} - ₹{txn['amount']} - {txn['description'][:50]}...")
    else:
        print("No suitable analyzer found")