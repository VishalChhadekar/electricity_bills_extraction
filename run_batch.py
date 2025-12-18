"""
Batch processing script - processes ALL files in input/ directory.
Supports PDF, JPG, JPEG, and PNG formats.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import main

if __name__ == "__main__":
    print("\n" + "="*60)
    print("BATCH PROCESSING MODE")
    print("="*60)
    print("\nThis will process ALL files in the input/ directory:")
    print("  • Supported formats: PDF, JPG, JPEG, PNG")
    print("  • Each file gets its own output files")
    print("  • Filenames: <original_name>_extracted.json")
    print("  • Filenames: <original_name>_accuracy_report.json")
    print("\n" + "="*60 + "\n")
    
    main()
