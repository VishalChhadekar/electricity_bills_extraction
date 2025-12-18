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
from utils.debug_logger import DebugLogger
from preprocessing.image_cleaner import preprocess_image
from ocr.google_ocr import perform_ocr, clean_ocr_text
from extraction.regex_extractor import extract_with_regex
from extraction.llm_extractor import extract_with_llm, merge_extractions
from evaluation.accuracy import evaluate_accuracy, evaluate_accuracy_from_file, generate_accuracy_report
from evaluation.ground_truth_matcher import load_ground_truth_file


def process_bill(input_path: str, ground_truth_list: list = None, verbose: bool = True, debug: bool = False, output_dir: str = None) -> dict:
    """
    Process a single bill through the complete pipeline.
    
    Pipeline:
    1. Load file (PDF → images or direct image)
    2. Preprocess each image (grayscale, denoise, threshold, deskew)
    3. Perform OCR using Google Vision
    4. Extract fields using regex
    5. Extract fields using LLM
    6. Merge results (LLM overrides regex)
    7. Evaluate accuracy if ground truth provided
    
    Args:
        input_path: Path to input bill (PDF or image)
        ground_truth_list: Optional list of ground truth entries from ground_truth.json
        verbose: If True, print detailed logs including OCR text and LLM interactions
        debug: If True, save detailed debug logs to output/debug_logs/
        output_dir: Output directory for debug logs
        
    Returns:
        Dictionary with extracted fields and accuracy (if ground truth provided)
    """
    print(f"\n{'='*60}")
    print(f"Processing: {input_path}")
    print(f"{'='*60}\n")
    
    # Extract filename for ground truth matching
    from pathlib import Path
    filename = Path(input_path).name
    
    # Initialize debug logger
    logger = DebugLogger(output_dir or "output", filename, enabled=debug)
    
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
    logger.log_raw_ocr(raw_text)
    ocr_text = clean_ocr_text(raw_text)
    logger.log_cleaned_ocr(ocr_text)
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
    logger.log_regex_extraction(regex_result)
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
    llm_result = extract_with_llm(ocr_text, verbose=verbose, logger=logger)
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
    print("\nStep 6: Merging results (LLM overrides regex)...")
    final_result = merge_extractions(regex_result, llm_result)
    logger.log_final_extraction(final_result)
    final_found = sum(1 for v in final_result.values() if v is not None)
    print(f"  → Final: {final_found}/11 fields")
    
    # Step 7: Evaluate accuracy if ground truth provided
    accuracy_data = None
    if ground_truth_list:
        print("\nStep 7: Evaluating accuracy...")
        accuracy_data = evaluate_accuracy_from_file(final_result, filename, ground_truth_list)
        logger.log_accuracy_evaluation(accuracy_data)
        if accuracy_data:
            print(f"  → Overall accuracy: {accuracy_data['overall_accuracy']}%")
        else:
            print(f"  → No ground truth found for: {filename}")
    
    # Save debug metadata
    logger.save_metadata()
    
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
    
    # Remove duplicates (Windows is case-insensitive, so *.pdf and *.PDF may match the same file)
    input_files = list(set(input_files))
    
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
    ground_truth_list = None
    if ground_truth_path.exists():
        print(f"\n{'='*60}")
        print("Loading ground truth data...")
        print(f"{'='*60}")
        try:
            ground_truth_list = load_ground_truth_file(str(ground_truth_path))
            print(f"✓ Loaded {len(ground_truth_list)} ground truth entries\n")
        except Exception as e:
            print(f"✗ Error loading ground truth: {e}")
            print("Accuracy evaluation will be skipped.\n")
            ground_truth_list = None
    else:
        print("ℹ️  No ground truth file found at expected/ground_truth.json")
        print("Accuracy evaluation will be skipped.\n")
    
    # Process each file
    results_summary = []
    
    for idx, input_path in enumerate(input_files, 1):
        print(f"\n{'#'*60}")
        print(f"Processing file {idx}/{len(input_files)}: {input_path.name}")
        print(f"{'#'*60}")
        
        try:
            result = process_bill(
                str(input_path),
                ground_truth_list,  # Pass the list instead of path
                verbose=False,  # Set to True for detailed logs
                debug=True,  # Enable debug logging
                output_dir=str(output_dir)
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
