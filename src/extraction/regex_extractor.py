"""
Regex-based field extraction module.
Extracts structured fields from OCR text using pattern matching.
"""

import re
from typing import Optional


def extract_with_regex(text: str) -> dict:
    """
    Extract fields using regex patterns.
    
    Business Logic:
    - Regex is fast and deterministic for well-structured fields
    - Handles common Indian bill formats and variations
    - Returns None for fields not found (never guesses)
    - Regex results override LLM results for reliability
    
    Args:
        text: OCR text from bill
        
    Returns:
        Dictionary with extracted fields (None if not found)
    """
    result = {
        "invoice_number": extract_invoice_number(text),
        "consumer_name": extract_consumer_name(text),
        "consumer_number": extract_consumer_number(text),
        "meter_number": extract_meter_number(text),
        "billing_period": extract_billing_period(text),
        "previous_reading_date": extract_previous_reading_date(text),
        "current_reading_date": extract_current_reading_date(text),
        "units_consumed": extract_units_consumed(text),
        "bill_amount": extract_bill_amount(text),
        "due_date": extract_due_date(text),
        "address": extract_address(text),
        "discom": extract_discom(text)
    }
    
    return result


def extract_invoice_number(text: str) -> Optional[str]:
    """Extract invoice/bill number - typically 10-20 digits."""
    patterns = [
        r'Invoice\\s*(?:No|Number)\\s*[:\\-]?\\s*([A-Z0-9]{8,20})',
        r'Bill\\s*(?:No|Number)\\s*[:\\-]?\\s*([A-Z0-9]{8,20})',
        r'Receipt\\s*(?:No|Number)\\s*[:\\-]?\\s*([A-Z0-9]{8,20})',
    ]
    return _find_first_match(text, patterns)


def extract_consumer_number(text: str) -> Optional[str]:
    """Extract consumer/account number - typically 10-15 digits."""
    patterns = [
        r'Consumer\s*(?:No|Number|ID)\s*[:\-]?\s*([A-Z0-9]{10,15})',
        r'Account\s*(?:No|Number)\s*[:\-]?\s*([A-Z0-9]{10,15})',
        r'CA\s*(?:No|Number)\s*[:\-]?\s*([A-Z0-9]{10,15})',
    ]
    return _find_first_match(text, patterns)


def extract_meter_number(text: str) -> Optional[str]:
    """Extract meter number - typically 8-12 digits."""
    patterns = [
        r'Meter\s*(?:No|Number)\s*[:\-]?\s*([A-Z0-9]{8,12})',
        r'Meter\s*ID\s*[:\-]?\s*([A-Z0-9]{8,12})',
    ]
    return _find_first_match(text, patterns)


def extract_consumer_name(text: str) -> Optional[str]:
    """Extract consumer name - typically after 'Name' label."""
    patterns = [
        r'(?:Consumer\s*)?Name\s*[:\-]?\s*([A-Z][A-Za-z\s\.]{2,50})',
        r'Bill\s*To\s*[:\-]?\s*([A-Z][A-Za-z\s\.]{2,50})',
    ]
    name = _find_first_match(text, patterns)
    return name.strip() if name else None


def extract_billing_period(text: str) -> Optional[str]:
    """Extract billing period - date range format."""
    patterns = [
        r'Billing\s*Period\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*(?:to|TO|-)\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Bill\s*Period\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*(?:to|TO|-)\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    return _find_first_match(text, patterns)


def extract_previous_reading_date(text: str) -> Optional[str]:
    """Extract previous meter reading date."""
    patterns = [
        r'Previous\s*(?:Reading\s*)?Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Last\s*Reading\s*Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    return _find_first_match(text, patterns)


def extract_current_reading_date(text: str) -> Optional[str]:
    """Extract current meter reading date."""
    patterns = [
        r'Current\s*(?:Reading\s*)?Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Present\s*Reading\s*Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    return _find_first_match(text, patterns)


def extract_units_consumed(text: str) -> Optional[str]:
    """Extract units consumed - typically in kWh."""
    patterns = [
        r'(?:Units\s*)?Consumed\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:kWh|Units)?',
        r'Total\s*Units\s*[:\-]?\s*(\d+(?:\.\d+)?)',
        r'Consumption\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:kWh|Units)?',
    ]
    return _find_first_match(text, patterns)


def extract_bill_amount(text: str) -> Optional[str]:
    """Extract total bill amount - typically with Rs or ₹."""
    patterns = [
        r'(?:Total\s*)?(?:Bill\s*)?Amount\s*(?:Payable)?\s*[:\-]?\s*(?:Rs\.?|₹)\s*(\d+(?:,\d+)*(?:\.\d{2})?)',
        r'(?:Total\s*)?(?:Bill\s*)?Amount\s*(?:Payable)?\s*[:\-]?\s*(\d+(?:,\d+)*(?:\.\d{2})?)',
        r'Amount\s*Due\s*[:\-]?\s*(?:Rs\.?|₹)\s*(\d+(?:,\d+)*(?:\.\d{2})?)',
    ]
    amount = _find_first_match(text, patterns)
    # Remove commas from amount
    return amount.replace(',', '') if amount else None


def extract_due_date(text: str) -> Optional[str]:
    """Extract payment due date."""
    patterns = [
        r'Due\s*Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Pay\s*(?:by|Before)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Payment\s*Due\s*Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    return _find_first_match(text, patterns)


def extract_address(text: str) -> Optional[str]:
    """Extract consumer address - typically multi-line."""
    patterns = [
        r'(?:Consumer\s*)?Address\s*[:\-]?\s*([A-Za-z0-9\s,\.\-/]{10,150})',
        r'Service\s*Address\s*[:\-]?\s*([A-Za-z0-9\s,\.\-/]{10,150})',
    ]
    address = _find_first_match(text, patterns)
    return address.strip() if address else None


def extract_discom(text: str) -> Optional[str]:
    """Extract DISCOM (Distribution Company) name."""
    # Common Indian DISCOMs
    discoms = [
        'MSEDCL', 'TATA Power', 'Adani Electricity', 'BSES',
        'BESCOM', 'KSEB', 'TANGEDCO', 'PSPCL', 'UPPCL',
        'Reliance Energy', 'Torrent Power'
    ]
    
    text_upper = text.upper()
    for discom in discoms:
        if discom.upper() in text_upper:
            return discom
    
    return None


def _find_first_match(text: str, patterns: list) -> Optional[str]:
    """
    Try multiple regex patterns and return first match.
    
    Args:
        text: Text to search
        patterns: List of regex patterns to try
        
    Returns:
        First matched group or None
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
