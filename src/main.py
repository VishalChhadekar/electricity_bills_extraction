"""
Main orchestration module for electricity bill extraction.
Coordinates the entire pipeline from file loading to accuracy evaluation.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load configuration and validate credentials
from config import validate_credentials

from utils.file_loader import load_file, save_json, load_json
from preprocessing.image_cleaner import preprocess_image
from ocr.google_ocr import perform_ocr, clean_ocr_text
from extraction.regex_extractor import extract_with_regex
from extraction.llm_extractor import extract_with_llm, merge_extractions
from evaluation.accuracy import evaluate_accuracy, generate_accuracy_report


def process_bill(input_path: str, ground_truth_path: str = None, verbose: bool = True) -> dict:
    """
    Process a single bill through the complete pipeline.
    
    Pipeline:
    1. Load file (PDF → images or direct image)
    2. Preprocess each image (grayscale, denoise, threshold, deskew)
    3. Perform OCR using Google Vision
    4. Extract fields using regex
    5. Extract fields using LLM
    6. Merge results (regex overrides LLM)
    7. Evaluate accuracy if ground truth provided
    
    Args:
        input_path: Path to input bill (PDF or image)
        ground_truth_path: Optional path to ground truth JSON
        verbose: If True, print detailed logs including OCR text and LLM interactions
        
    Returns:
        Dictionary with extracted fields and accuracy (if ground truth provided)
    """
    print(f"\n{'='*60}")
    print(f"Processing: {input_path}")
    print(f"{'='*60}\n")
    
    # Step 1: Load file
    print("Step 1: Loading file...")
    images = load_file(input_path)
    print(f"  → Loaded {len(images)} image(s)")
    
    # Process first page/image only (can be extended for multi-page)
    image = images[0]
    
    # Step 2: Preprocess image
    print("\nStep 2: Preprocessing image...")
    preprocessed = preprocess_image(image)
    print("  → Applied grayscale, denoise, threshold, deskew")
    
    # Step 3: Perform OCR
    print("\nStep 3: Performing OCR...")
    raw_text = perform_ocr(preprocessed)
    ocr_text = clean_ocr_text(raw_text)
    print(f"  → Extracted {len(ocr_text)} characters")
    
    if verbose:
        print("\n" + "-"*60)
        print("OCR OUTPUT (Full Text):")
        print("-"*60)
        print(ocr_text)
        print("-"*60)
    
    # Step 4: Extract with regex
    print("\nStep 4: Extracting fields with regex...")
    regex_result = extract_with_regex(ocr_text)
    regex_found = sum(1 for v in regex_result.values() if v is not None)
    print(f"  → Found {regex_found}/11 fields")
    
    if verbose:
        print("\n" + "-"*60)
        print("REGEX EXTRACTION RESULTS:")
        print("-"*60)
        import json
        print(json.dumps(regex_result, indent=2, ensure_ascii=False))
        print("-"*60)
    
    # Step 5: Extract with LLM
    print("\nStep 5: Extracting fields with LLM...")
    llm_result = extract_with_llm(ocr_text, verbose=verbose)
    llm_found = sum(1 for v in llm_result.values() if v is not None)
    print(f"  → Found {llm_found}/11 fields")
    
    if verbose:
        print("\n" + "-"*60)
        print("LLM EXTRACTION RESULTS:")
        print("-"*60)
        import json
        print(json.dumps(llm_result, indent=2, ensure_ascii=False))
        print("-"*60)
    
    # Step 6: Merge results
    print("\nStep 6: Merging results (regex overrides LLM)...")
    final_result = merge_extractions(regex_result, llm_result)
    final_found = sum(1 for v in final_result.values() if v is not None)
    print(f"  → Final: {final_found}/11 fields")
    
    # Step 7: Evaluate accuracy if ground truth provided
    accuracy_data = None
    if ground_truth_path and os.path.exists(ground_truth_path):
        print("\nStep 7: Evaluating accuracy...")
        ground_truth = load_json(ground_truth_path)
        accuracy_data = evaluate_accuracy(final_result, ground_truth)
        print(f"  → Overall accuracy: {accuracy_data['overall_accuracy']}%")
    
    return {
        "extracted": final_result,
        "accuracy": accuracy_data,
        "ocr_text": ocr_text  # Include for debugging
    }


def main():
    """
    Main entry point.
    
    Business Logic:
    - Validates credentials before processing
    - Processes ALL files in input/ directory (PDF, JPG, PNG)
    - Looks for ground truth in expected/ directory (optional)
    - Saves results to output/ directory with timestamped filenames
    - Generates both JSON and human-readable report for each file
    """
    # Validate credentials first
    print("\n" + "="*60)
    print("Validating credentials...")
    print("="*60 + "\n")
    
    is_valid, errors = validate_credentials()
    if not is_valid:
        print("\n❌ Configuration errors found:\n")
        for error in errors:
            print(f"  {error}")
        print("\nPlease check your .env file and ensure all credentials are set.")
        sys.exit(1)
    
    print("\n✅ All credentials validated successfully!\n")
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "input"
    expected_dir = project_root / "expected"
    output_dir = project_root / "output"
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Find ALL input files (PDF, JPG, PNG)
    input_files = []
    # SUPPORTED FILE FORMATS
    for ext in ['*.pdf', '*.PDF', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
        input_files.extend(list(input_dir.glob(ext)))
    
    if not input_files:
        print("❌ Error: No input files found in input/ directory")
        print("Supported formats: PDF, JPG, JPEG, PNG")
        print(f"Please add files to: {input_dir}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Found {len(input_files)} file(s) to process:")
    print(f"{'='*60}")
    for i, file in enumerate(input_files, 1):
        print(f"  {i}. {file.name}")
    print(f"{'='*60}\n")
    
    # Check for ground truth
    ground_truth_path = expected_dir / "ground_truth.json"
    if not ground_truth_path.exists():
        print("ℹ️  No ground truth file found at expected/ground_truth.json")
        print("Accuracy evaluation will be skipped.\n")
        ground_truth_path = None
    
    # Process each file
    results_summary = []
    
    for idx, input_path in enumerate(input_files, 1):
        print(f"\n{'#'*60}")
        print(f"Processing file {idx}/{len(input_files)}: {input_path.name}")
        print(f"{'#'*60}")
        
        try:
            result = process_bill(
                str(input_path),
                str(ground_truth_path) if ground_truth_path else None,
                verbose=False  # Set to True for detailed logs
            )
            
            # Generate output filename based on input filename
            base_name = input_path.stem  # filename without extension
            
            # Save extracted data
            extracted_path = output_dir / f"{base_name}_extracted.json"
            save_json(result["extracted"], str(extracted_path))
            print(f"\n✓ Saved extracted data to: {extracted_path}")
            
            # Save accuracy report if available
            if result["accuracy"]:
                accuracy_path = output_dir / f"{base_name}_accuracy_report.json"
                save_json(result["accuracy"], str(accuracy_path))
                print(f"✓ Saved accuracy report to: {accuracy_path}")
                
                # Store summary
                results_summary.append({
                    "file": input_path.name,
                    "accuracy": result["accuracy"]["overall_accuracy"],
                    "correct_fields": result["accuracy"]["correct_fields"],
                    "total_fields": result["accuracy"]["total_fields"]
                })
            else:
                results_summary.append({
                    "file": input_path.name,
                    "status": "Processed (no ground truth)"
                })
            
        except Exception as e:
            print(f"\n✗ Error processing {input_path.name}: {e}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                "file": input_path.name,
                "status": "Failed",
                "error": str(e)
            })
            continue
    
    # Print final summary
    print(f"\n\n{'='*60}")
    print("PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total files processed: {len(input_files)}")
    print(f"{'='*60}\n")
    
    for i, summary in enumerate(results_summary, 1):
        print(f"{i}. {summary['file']}")
        if 'accuracy' in summary:
            print(f"   Accuracy: {summary['accuracy']}% ({summary['correct_fields']}/{summary['total_fields']} fields)")
        elif 'error' in summary:
            print(f"   Status: ❌ {summary['status']} - {summary['error']}")
        else:
            print(f"   Status: ✓ {summary['status']}")
        print()
    
    print(f"{'='*60}")
    print("All processing complete!")
    print(f"Results saved to: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
