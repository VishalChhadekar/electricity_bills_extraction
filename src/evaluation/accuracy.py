"""
Accuracy evaluation module.
Compares extracted fields with ground truth and calculates accuracy metrics.
"""

from typing import Dict, Tuple


def evaluate_accuracy(extracted: dict, ground_truth: dict) -> dict:
    """
    Calculate field-level and overall accuracy.
    
    Business Logic:
    - Exact match after normalization (case-insensitive, whitespace-trimmed)
    - Each field is binary: correct (1) or incorrect (0)
    - Overall accuracy = correct_fields / total_fields
    - Null values in ground truth are considered "not applicable"
    
    Args:
        extracted: Extracted fields dictionary
        ground_truth: Expected values dictionary
        
    Returns:
        Dictionary with accuracy metrics and field-level results
    """
    field_results = {}
    correct_count = 0
    total_count = 0
    
    # Evaluate each field
    for field, expected_value in ground_truth.items():
        # Skip fields not in ground truth (shouldn't happen with strict schema)
        if field not in extracted:
            continue
        
        extracted_value = extracted[field]
        
        # Compare normalized values
        is_correct = _compare_values(extracted_value, expected_value)
        
        field_results[field] = {
            "expected": expected_value,
            "extracted": extracted_value,
            "correct": is_correct
        }
        
        # Only count fields that have ground truth values
        if expected_value is not None:
            total_count += 1
            if is_correct:
                correct_count += 1
    
    # Calculate overall accuracy
    overall_accuracy = (correct_count / total_count * 100) if total_count > 0 else 0.0
    
    return {
        "overall_accuracy": round(overall_accuracy, 2),
        "correct_fields": correct_count,
        "total_fields": total_count,
        "field_results": field_results
    }


def _compare_values(extracted, expected) -> bool:
    """
    Compare two values with normalization.
    
    Business Logic:
    - Both None/null = match
    - One None, one not = no match
    - Strings: case-insensitive, whitespace-trimmed, punctuation-normalized
    - Numbers: string comparison after normalization
    
    Args:
        extracted: Extracted value
        expected: Expected value
        
    Returns:
        True if values match, False otherwise
    """
    # Both None = match
    if extracted is None and expected is None:
        return True
    
    # One None, one not = no match
    if extracted is None or expected is None:
        return False
    
    # Normalize both to strings
    extracted_str = _normalize_string(str(extracted))
    expected_str = _normalize_string(str(expected))
    
    return extracted_str == expected_str


def _normalize_string(value: str) -> str:
    """
    Normalize string for comparison.
    
    Normalization steps:
    - Convert to lowercase
    - Strip whitespace
    - Remove common punctuation variations
    - Normalize date separators
    
    Args:
        value: String to normalize
        
    Returns:
        Normalized string
    """
    import re
    
    # Convert to lowercase and strip
    normalized = value.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Normalize common punctuation
    normalized = normalized.replace(',', '')  # Remove commas from numbers
    normalized = normalized.replace('rs.', 'rs')
    normalized = normalized.replace('₹', 'rs')
    
    # Normalize date separators to single format
    normalized = normalized.replace('/', '-')
    
    return normalized


def generate_accuracy_report(accuracy_data: dict) -> str:
    """
    Generate human-readable accuracy report.
    
    Args:
        accuracy_data: Accuracy evaluation results
        
    Returns:
        Formatted report string
    """
    report_lines = [
        "=" * 60,
        "ACCURACY REPORT",
        "=" * 60,
        f"\nOverall Accuracy: {accuracy_data['overall_accuracy']}%",
        f"Correct Fields: {accuracy_data['correct_fields']}/{accuracy_data['total_fields']}",
        "\n" + "-" * 60,
        "Field-Level Results:",
        "-" * 60
    ]
    
    for field, result in accuracy_data['field_results'].items():
        status = "✓ CORRECT" if result['correct'] else "✗ INCORRECT"
        report_lines.append(f"\n{field}:")
        report_lines.append(f"  Expected:  {result['expected']}")
        report_lines.append(f"  Extracted: {result['extracted']}")
        report_lines.append(f"  Status:    {status}")
    
    report_lines.append("\n" + "=" * 60)
    
    return "\n".join(report_lines)
