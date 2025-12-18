"""
Evaluation Report Generator
Compares extracted results from /output directory against ground_truth.json
and generates comprehensive accuracy metrics.

Usage:
    python evaluate_results.py
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import re


def normalize_string(value: str) -> str:
    """
    Normalize string for comparison.
    
    Normalization steps:
    - Convert to lowercase
    - Strip whitespace
    - Remove common punctuation variations
    - Normalize date separators
    """
    if value is None:
        return ""
    
    # Convert to lowercase and strip
    normalized = str(value).lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove commas from numbers
    normalized = normalized.replace(',', '')
    
    # Normalize date separators to single format
    normalized = normalized.replace('/', '-')
    normalized = normalized.replace('.', '-')
    
    return normalized


def compare_values(extracted, expected) -> bool:
    """
    Compare two values with normalization.
    
    Returns:
        True if values match, False otherwise
    """
    # Both None/empty = match
    if (extracted is None or extracted == "") and (expected is None or expected == ""):
        return True
    
    # One None, one not = no match
    if (extracted is None or extracted == "") or (expected is None or expected == ""):
        return False
    
    # Normalize both to strings
    extracted_str = normalize_string(str(extracted))
    expected_str = normalize_string(str(expected))
    
    return extracted_str == expected_str


def load_ground_truth(path: str) -> List[Dict]:
    """Load ground truth JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_extracted_result(path: str) -> Dict:
    """Load extracted result JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_ground_truth_by_filename(ground_truth_list: List[Dict], filename: str) -> Dict:
    """Find ground truth entry matching the given filename."""
    base_filename = Path(filename).name.lower()
    
    for entry in ground_truth_list:
        gt_filename = entry.get('file_name', '').lower()
        if gt_filename == base_filename:
            return entry
    
    return None


def evaluate_single_file(extracted: Dict, ground_truth_entry: Dict) -> Dict:
    """
    Evaluate a single file against its ground truth.
    
    Returns:
        Dictionary with field-level results and overall accuracy
    """
    field_results = {}
    correct_count = 0
    total_count = 0
    
    # Define field mappings: (extracted_key, ground_truth_key, field_name)
    field_mappings = [
        ('invoice_number', 'invoiceNumber', 'Invoice Number'),
        ('previous_reading_date', 'previousReadingDate', 'Previous Reading Date'),
        ('current_reading_date', 'presentReadingDate', 'Present Reading Date'),
    ]
    
    # Evaluate top-level fields
    for extracted_key, gt_key, field_name in field_mappings:
        expected_value = ground_truth_entry.get(gt_key)
        extracted_value = extracted.get(extracted_key)
        
        # Only evaluate if ground truth has a value
        if expected_value and expected_value != "NA":
            total_count += 1
            is_correct = compare_values(extracted_value, expected_value)
            if is_correct:
                correct_count += 1
            
            field_results[field_name] = {
                'expected': expected_value,
                'extracted': extracted_value,
                'correct': is_correct
            }
    
    # Evaluate meter readings (first meter only)
    meter_readings = ground_truth_entry.get('meterReadings', [])
    if meter_readings and len(meter_readings) > 0:
        first_meter = meter_readings[0]
        
        # Meter Number
        expected_meter = first_meter.get('meterNumber') or first_meter.get('expected_meter_number')
        extracted_meter = extracted.get('meter_number')
        
        if expected_meter:
            total_count += 1
            is_correct = compare_values(extracted_meter, expected_meter)
            if is_correct:
                correct_count += 1
            
            field_results['Meter Number'] = {
                'expected': expected_meter,
                'extracted': extracted_meter,
                'correct': is_correct
            }
        
        # Units Consumed
        expected_units = first_meter.get('unitsConsumed') or first_meter.get('expected_unit_consumption')
        extracted_units = extracted.get('units_consumed')
        
        if expected_units:
            total_count += 1
            is_correct = compare_values(extracted_units, expected_units)
            if is_correct:
                correct_count += 1
            
            field_results['Units Consumed'] = {
                'expected': expected_units,
                'extracted': extracted_units,
                'correct': is_correct
            }
    
    # Calculate overall accuracy
    overall_accuracy = (correct_count / total_count * 100) if total_count > 0 else 0.0
    
    return {
        'overall_accuracy': round(overall_accuracy, 2),
        'correct_fields': correct_count,
        'total_fields': total_count,
        'field_results': field_results
    }


def generate_report(results: List[Dict]) -> str:
    """Generate comprehensive evaluation report."""
    
    lines = []
    lines.append("=" * 100)
    lines.append("ELECTRICITY BILL EXTRACTION - EVALUATION REPORT")
    lines.append("=" * 100)
    lines.append("")
    
    # Individual file results
    lines.append("INDIVIDUAL FILE ACCURACY")
    lines.append("-" * 100)
    lines.append("")
    
    total_accuracy = 0
    total_files = 0
    total_correct = 0
    total_fields = 0
    
    for result in results:
        if result['status'] == 'evaluated':
            total_files += 1
            total_accuracy += result['accuracy']['overall_accuracy']
            total_correct += result['accuracy']['correct_fields']
            total_fields += result['accuracy']['total_fields']
            
            lines.append(f"File: {result['filename']}")
            lines.append(f"  Accuracy: {result['accuracy']['overall_accuracy']}%")
            lines.append(f"  Correct Fields: {result['accuracy']['correct_fields']}/{result['accuracy']['total_fields']}")
            lines.append("")
            
            # Field-level details
            for field_name, field_data in result['accuracy']['field_results'].items():
                status = "✓" if field_data['correct'] else "✗"
                lines.append(f"    {status} {field_name}:")
                lines.append(f"       Expected:  {field_data['expected']}")
                lines.append(f"       Extracted: {field_data['extracted']}")
            lines.append("")
            lines.append("-" * 100)
            lines.append("")
        elif result['status'] == 'no_ground_truth':
            lines.append(f"File: {result['filename']}")
            lines.append(f"  Status: No ground truth available")
            lines.append("")
            lines.append("-" * 100)
            lines.append("")
        elif result['status'] == 'no_extraction':
            lines.append(f"File: {result['filename']}")
            lines.append(f"  Status: No extracted result found")
            lines.append("")
            lines.append("-" * 100)
            lines.append("")
    
    # Overall summary
    lines.append("")
    lines.append("=" * 100)
    lines.append("OVERALL SUMMARY")
    lines.append("=" * 100)
    lines.append("")
    lines.append(f"Total Files Evaluated: {total_files}")
    lines.append(f"Total Fields Evaluated: {total_fields}")
    lines.append(f"Total Correct Fields: {total_correct}")
    lines.append(f"Total Incorrect Fields: {total_fields - total_correct}")
    lines.append("")
    
    if total_files > 0:
        avg_accuracy = total_accuracy / total_files
        lines.append(f"AVERAGE ACCURACY: {avg_accuracy:.2f}%")
        lines.append(f"FIELD-LEVEL ACCURACY: {(total_correct / total_fields * 100):.2f}%")
    else:
        lines.append("AVERAGE ACCURACY: N/A (no files evaluated)")
    
    lines.append("")
    lines.append("=" * 100)
    
    return "\n".join(lines)


def main():
    """Main evaluation function."""
    
    # Define paths
    project_root = Path(__file__).parent
    ground_truth_path = project_root / "expected" / "ground_truth.json"
    output_dir = project_root / "output"
    
    print("\n" + "=" * 100)
    print("ELECTRICITY BILL EXTRACTION - EVALUATION SCRIPT")
    print("=" * 100 + "\n")
    
    # Load ground truth
    if not ground_truth_path.exists():
        print(f"❌ Error: Ground truth file not found at {ground_truth_path}")
        return
    
    print(f"Loading ground truth from: {ground_truth_path}")
    ground_truth_list = load_ground_truth(str(ground_truth_path))
    print(f"✓ Loaded {len(ground_truth_list)} ground truth entries\n")
    
    # Process each ground truth entry
    results = []
    
    for gt_entry in ground_truth_list:
        filename = gt_entry['file_name']
        base_name = Path(filename).stem
        
        # Look for extracted file
        extracted_file = output_dir / f"{base_name}_extracted.json"
        
        if not extracted_file.exists():
            print(f"⚠ No extraction found for: {filename}")
            results.append({
                'filename': filename,
                'status': 'no_extraction'
            })
            continue
        
        # Load extracted result
        extracted = load_extracted_result(str(extracted_file))
        
        # Evaluate
        accuracy = evaluate_single_file(extracted, gt_entry)
        
        print(f"✓ Evaluated: {filename} - Accuracy: {accuracy['overall_accuracy']}%")
        
        results.append({
            'filename': filename,
            'status': 'evaluated',
            'accuracy': accuracy
        })
    
    # Generate report
    print("\n" + "=" * 100)
    print("Generating evaluation report...")
    print("=" * 100 + "\n")
    
    report = generate_report(results)
    
    # Save report to file
    report_path = output_dir / "evaluation_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ Report saved to: {report_path}\n")
    
    # Save detailed JSON results
    json_report_path = output_dir / "evaluation_report.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Detailed JSON report saved to: {json_report_path}\n")
    
    # Print report to console
    print("\n" + report)


if __name__ == "__main__":
    main()
