"""
Ground truth matching module.
Handles loading and matching ground truth data by filename.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path


def load_ground_truth_file(path: str) -> List[Dict]:
    """
    Load ground truth JSON file.
    
    Args:
        path: Path to ground_truth.json file
        
    Returns:
        List of ground truth entries
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_ground_truth_by_filename(ground_truth_list: List[Dict], filename: str) -> Optional[Dict]:
    """
    Find ground truth entry matching the given filename.
    
    Performs case-insensitive matching on the base filename.
    
    Args:
        ground_truth_list: List of ground truth entries
        filename: Filename to match (e.g., "AJMER-RAJASTHAN.pdf")
        
    Returns:
        Matching ground truth entry or None if not found
    """
    # Extract base filename (with extension)
    base_filename = Path(filename).name.lower()
    
    for entry in ground_truth_list:
        gt_filename = entry.get('file_name', '').lower()
        if gt_filename == base_filename:
            return entry
    
    return None


def transform_ground_truth_to_flat(ground_truth_entry: Dict) -> Dict:
    """
    Transform nested ground truth structure to flat format for comparison.
    
    Maps ground truth field names to extraction output field names:
    - invoiceNumber -> invoice_number
    - previousReadingDate -> previous_reading_date
    - presentReadingDate -> current_reading_date
    - meterReadings[0].meterNumber -> meter_number
    - meterReadings[0].unitsConsumed -> units_consumed
    
    Note: Currently only handles the first meter reading.
    
    Args:
        ground_truth_entry: Ground truth entry from JSON
        
    Returns:
        Flat dictionary matching extraction output format
    """
    flat_dict = {}
    
    # Map top-level fields
    if 'invoiceNumber' in ground_truth_entry:
        flat_dict['invoice_number'] = ground_truth_entry['invoiceNumber']
    
    if 'previousReadingDate' in ground_truth_entry:
        flat_dict['previous_reading_date'] = ground_truth_entry['previousReadingDate']
    
    if 'presentReadingDate' in ground_truth_entry:
        flat_dict['current_reading_date'] = ground_truth_entry['presentReadingDate']
    
    # Map meter readings (first meter only for now)
    meter_readings = ground_truth_entry.get('meterReadings', [])
    if meter_readings and len(meter_readings) > 0:
        first_meter = meter_readings[0]
        
        # Handle both 'meterNumber' and 'expected_meter_number' keys
        if 'meterNumber' in first_meter:
            flat_dict['meter_number'] = first_meter['meterNumber']
        elif 'expected_meter_number' in first_meter:
            flat_dict['meter_number'] = first_meter['expected_meter_number']
        
        # Handle both 'unitsConsumed' and 'expected_unit_consumption' keys
        if 'unitsConsumed' in first_meter:
            flat_dict['units_consumed'] = first_meter['unitsConsumed']
        elif 'expected_unit_consumption' in first_meter:
            flat_dict['units_consumed'] = first_meter['expected_unit_consumption']
    
    # Add placeholder None values for other expected fields
    # This ensures all fields are present in the comparison
    expected_fields = [
        'consumer_name', 'consumer_address', 'billing_period',
        'due_date', 'total_amount', 'previous_reading', 'current_reading'
    ]
    
    for field in expected_fields:
        if field not in flat_dict:
            flat_dict[field] = None
    
    return flat_dict
