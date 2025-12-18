"""
Simple script to run extraction with verbose logging enabled.
Shows OCR output, LLM prompts/responses, and all intermediate results.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import process_bill

# Define paths
project_root = Path(__file__).parent
input_dir = project_root / "input"
expected_dir = project_root / "expected"

# Find input file
input_files = list(input_dir.glob("sample_bill.*"))
if not input_files:
    print("Error: No input file found in input/ directory")
    sys.exit(1)

input_path = input_files[0]

# Check for ground truth
ground_truth_path = expected_dir / "ground_truth.json"
if not ground_truth_path.exists():
    ground_truth_path = None

# Run with verbose logging
print("\n" + "="*60)
print("VERBOSE EXTRACTION MODE")
print("="*60)
print("\nThis will show:")
print("  • Full OCR text output")
print("  • Regex extraction results")
print("  • LLM prompt sent to OpenAI")
print("  • LLM response received")
print("  • Token usage statistics")
print("  • Final merged results")
print("\n" + "="*60 + "\n")

result = process_bill(
    str(input_path),
    str(ground_truth_path) if ground_truth_path else None,
    verbose=True  # Enable verbose logging
)

print("\n" + "="*60)
print("VERBOSE EXTRACTION COMPLETE")
print("="*60 + "\n")
