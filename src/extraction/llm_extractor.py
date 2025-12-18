"""
LLM-based field extraction module.
Uses OpenAI GPT-4o-mini to extract fields that regex may miss.
"""

import os
import json
from openai import OpenAI


# Strict JSON schema for bill fields
BILL_SCHEMA = {
    "invoice_number": None,
    "consumer_name": None,
    "consumer_number": None,
    "meter_number": None,
    "billing_period": None,
    "previous_reading_date": None,
    "current_reading_date": None,
    "units_consumed": None,
    "bill_amount": None,
    "due_date": None,
    "address": None,
    "discom": None
}


def extract_with_llm(ocr_text: str, verbose: bool = False, logger=None) -> dict:
    """
    Extract fields using OpenAI LLM.
    
    Business Logic:
    - LLM handles unstructured/varying bill formats better than regex
    - Temperature=0 for deterministic output
    - Strict JSON schema prevents hallucination
    - Falls back to None for missing fields (never guesses)
    
    Args:
        ocr_text: OCR text from bill
        verbose: If True, print prompt and response details
        logger: Optional DebugLogger instance for detailed logging
        
    Returns:
        Dictionary with extracted fields
        
    Raises:
        Exception: If OpenAI API key is not configured
    """
    # Verify API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise Exception(
            "OPENAI_API_KEY environment variable not set. "
            "Please set it to your OpenAI API key."
        )
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Build prompt with strict instructions
    prompt = _build_extraction_prompt(ocr_text)
    
    system_message = "You are a precise data extraction assistant. Extract only what is explicitly present in the text. Return valid JSON only."
    
    # Log prompt if logger is provided
    if logger:
        logger.log_llm_prompt(system_message, prompt, model="gpt-4o-mini")
    
    if verbose:
        print("\n" + "="*60)
        print("LLM PROMPT SENT TO OPENAI:")
        print("="*60)
        print(f"Model: gpt-4o-mini")
        print(f"Temperature: 0")
        print(f"Response Format: JSON")
        print("\n" + "-"*60)
        print("System Message:")
        print("-"*60)
        print(system_message)
        print("\n" + "-"*60)
        print("User Prompt:")
        print("-"*60)
        print(prompt)
        print("="*60)
    
    try:
        # Call GPT-4o-mini with temperature=0 for deterministic output
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,  # Deterministic output
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        # Parse response
        result_text = response.choices[0].message.content
        
        # Log response if logger is provided
        if logger:
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            logger.log_llm_response(result_text, usage=usage_dict, model=response.model)
        
        if verbose:
            print("\n" + "="*60)
            print("LLM RESPONSE FROM OPENAI:")
            print("="*60)
            print(f"Model: {response.model}")
            print(f"Tokens Used - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
            print("\n" + "-"*60)
            print("Raw Response:")
            print("-"*60)
            print(result_text)
            print("="*60)
        
        result = json.loads(result_text)
        
        # Ensure all expected fields are present
        for field in BILL_SCHEMA:
            if field not in result:
                result[field] = None
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Warning: LLM returned invalid JSON: {e}")
        if verbose:
            print(f"Failed to parse: {result_text}")
        return BILL_SCHEMA.copy()
    except Exception as e:
        print(f"Warning: LLM extraction failed: {e}")
        return BILL_SCHEMA.copy()


def _build_extraction_prompt(ocr_text: str) -> str:
    """
    Build extraction prompt for LLM with few-shot examples.
    
    Business Logic:
    - Few-shot examples teach LLM the expected extraction pattern
    - Detailed field descriptions with common label variations
    - Clear instructions prevent hallucination
    - Examples from actual Indian electricity bills
    
    Args:
        ocr_text: OCR text to extract from
        
    Returns:
        Formatted prompt string with examples
    """
    prompt = f"""You are an expert at extracting structured data from Indian electricity bills.

IMPORTANT INSTRUCTIONS:
1. Extract fields EXACTLY as they appear in the OCR text
2. If a field is missing or unclear, return null
3. Do NOT guess or infer values
4. Pay attention to common label variations across different states
5. Return ONLY valid JSON matching the schema

---
EXAMPLE 1 - Rajasthan Bill:
---
OCR Text:
AJMER VIDYUT VITRAN NIGAM LTD
Invoice No: 12022203035729
Consumer Name: RAJESH KUMAR
Consumer No: 0802/0037
Meter No: 4943282
Billing Period: May/2024
Previous Reading Date: 30-03-2024
Current Reading Date: 30-04-2024
Units Consumed: 753
Total Amount: Rs. 5600.00
Due Date: 22-05-2024

Correct Extraction:
{{
  "invoice_number": "12022203035729",
  "consumer_name": "RAJESH KUMAR",
  "consumer_number": "0802/0037",
  "meter_number": "4943282",
  "billing_period": "May/2024",
  "previous_reading_date": "30-03-2024",
  "current_reading_date": "30-04-2024",
  "units_consumed": "753",
  "bill_amount": "5600.00",
  "due_date": "22-05-2024",
  "address": null,
  "discom": "AJMER VIDYUT VITRAN NIGAM LTD"
}}

---
EXAMPLE 2 - Maharashtra Bill:
---
OCR Text:
MSEDCL - Maharashtra State Electricity Distribution Co Ltd
Bill Number: 000002436874795
Account Number: 000002436874795
Meter Serial No: 06507161895
Bill Month: MAY-24
Last Reading: 11-APR-24
Current Reading: 11-MAY-24
Consumption: 486 Units
Bill Amount: 3250
Payment Due: 25-MAY-24

Correct Extraction:
{{
  "invoice_number": "000002436874795",
  "consumer_name": null,
  "consumer_number": "000002436874795",
  "meter_number": "06507161895",
  "billing_period": "MAY-24",
  "previous_reading_date": "11-APR-24",
  "current_reading_date": "11-MAY-24",
  "units_consumed": "486",
  "bill_amount": "3250",
  "due_date": "25-MAY-24",
  "address": null,
  "discom": "MSEDCL"
}}

---
FIELD DESCRIPTIONS & COMMON LABELS:
---

1. invoice_number: Bill/Invoice number (unique identifier for the bill)
   Common labels: "Invoice No", "Bill No", "Bill Number", "Invoice Number", "बिल संख्या", "Receipt No"
   
2. consumer_name: Full name of the electricity consumer
   Common labels: "Consumer Name", "Name", "Customer Name", "उपभोक्ता का नाम"
   
3. consumer_number: Consumer/Account/Customer number (alphanumeric, may include slashes or hyphens)
   Common labels: "Consumer No", "Account No", "Customer No", "CA No", "Consumer Number", "खाता संख्या"
   
4. meter_number: Electricity meter serial number (usually 6-10 digits, may have prefix)
   Common labels: "Meter No", "Meter Number", "Meter Serial No", "MTR NO", "मीटर नंबर", "Meter S.No"
   
5. billing_period: Billing period or bill month
   Common labels: "Billing Period", "Bill Month", "Period", "Bill For", "बिलिंग अवधि"
   
6. previous_reading_date: Date of previous/last meter reading
   Common labels: "Previous Reading Date", "Last Reading", "Prev Reading", "पिछली रीडिंग", "Previous Date"
   Formats: DD-MM-YYYY, DD/MM/YYYY, DD-MMM-YY, DD.MM.YYYY
   
7. current_reading_date: Date of current/present meter reading
   Common labels: "Current Reading Date", "Present Reading", "Reading Date", "वर्तमान रीडिंग", "Current Date"
   Formats: DD-MM-YYYY, DD/MM/YYYY, DD-MMM-YY, DD.MM.YYYY
   
8. units_consumed: Total electricity units consumed (number, may have decimals)
   Common labels: "Units Consumed", "Consumption", "Total Units", "Energy Consumed", "खपत इकाइयाँ", "kWh"
   
9. bill_amount: Total bill amount (number, extract without currency symbol)
   Common labels: "Total Amount", "Bill Amount", "Amount Payable", "Net Amount", "कुल राशि", "Total"
   
10. due_date: Payment due date
    Common labels: "Due Date", "Payment Due Date", "Last Date", "Pay By", "भुगतान तिथि"
    Formats: DD-MM-YYYY, DD/MM/YYYY, DD-MMM-YY
   
11. address: Consumer's address (full address if available)
    Common labels: "Address", "Consumer Address", "पता", "Service Address"
    
12. discom: Distribution company name (electricity board/company)
    Common labels: Usually appears at top of bill as company name
    Examples: "MSEDCL", "BESCOM", "TPCODL", "AJMER VIDYUT VITRAN NIGAM LTD"

---
NOW EXTRACT FROM THIS BILL:
---

OCR Text:
{ocr_text}

Return JSON in this exact format:
{{
  "invoice_number": null,
  "consumer_name": null,
  "consumer_number": null,
  "meter_number": null,
  "billing_period": null,
  "previous_reading_date": null,
  "current_reading_date": null,
  "units_consumed": null,
  "bill_amount": null,
  "due_date": null,
  "address": null,
  "discom": null
}}
"""
    return prompt


def merge_extractions(regex_result: dict, llm_result: dict) -> dict:
    """
    Merge regex and LLM results, with LLM taking precedence.
    
    Business Logic:
    - LLM is more accurate for complex/varying bill formats (based on testing)
    - Regex fills gaps where LLM fails to extract
    - LLM overrides regex to prevent regex false positives
    
    Strategy Change (2025-12-18):
    - Previously: Regex took precedence (caused 0.000 units consumed error)
    - Now: LLM takes precedence (80% accuracy vs regex errors)
    
    Args:
        regex_result: Results from regex extraction
        llm_result: Results from LLM extraction
        
    Returns:
        Merged dictionary with best results from both
    """
    merged = {}
    
    for field in BILL_SCHEMA:
        # LLM takes precedence if it found a value
        llm_value = llm_result.get(field)
        regex_value = regex_result.get(field)
        
        if llm_value is not None and llm_value != "":
            # Use LLM value
            merged[field] = llm_value
        elif regex_value is not None and regex_value != "":
            # Fall back to regex if LLM didn't find it
            merged[field] = regex_value
        else:
            # Both failed
            merged[field] = None
    
    return merged
