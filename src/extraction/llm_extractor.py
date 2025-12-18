"""
LLM-based field extraction module.
Uses OpenAI GPT-4o-mini to extract fields that regex may miss.
"""

import os
import json
from openai import OpenAI


# Strict JSON schema for bill fields
BILL_SCHEMA = {
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


def extract_with_llm(ocr_text: str, verbose: bool = False) -> dict:
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
        print("You are a precise data extraction assistant. Extract only what is explicitly present in the text. Return valid JSON only.")
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
                    "content": "You are a precise data extraction assistant. Extract only what is explicitly present in the text. Return valid JSON only."
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
    Build extraction prompt for LLM.
    
    Business Logic:
    - Clear instructions prevent hallucination
    - Schema definition ensures consistent output
    - Examples would go here in production
    
    Args:
        ocr_text: OCR text to extract from
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are given OCR text from an Indian electricity bill.

Extract the following fields exactly as they appear in the text.
If a field is missing or unclear, return null.
Do not guess or infer values.
Return ONLY valid JSON matching the schema below.

Required fields:
- consumer_name: Full name of the consumer
- consumer_number: Consumer/account number (alphanumeric)
- meter_number: Electricity meter number
- billing_period: Billing period (date range)
- previous_reading_date: Previous meter reading date
- current_reading_date: Current meter reading date
- units_consumed: Total units consumed (number)
- bill_amount: Total bill amount (number, without currency symbol)
- due_date: Payment due date
- address: Consumer address
- discom: Distribution company name

OCR Text:
{ocr_text}

Return JSON in this exact format:
{{
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
    Merge regex and LLM results, with regex taking precedence.
    
    Business Logic:
    - Regex is more reliable for structured fields (when it matches)
    - LLM fills gaps where regex fails
    - Regex overrides LLM to prevent hallucination
    
    Args:
        regex_result: Results from regex extraction
        llm_result: Results from LLM extraction
        
    Returns:
        Merged dictionary with best results from both
    """
    merged = {}
    
    for field in BILL_SCHEMA:
        # Regex takes precedence if it found a value
        if regex_result.get(field):
            merged[field] = regex_result[field]
        # Otherwise use LLM result (may be None)
        else:
            merged[field] = llm_result.get(field)
    
    return merged
