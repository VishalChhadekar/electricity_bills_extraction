"""
Debug logging utility for electricity bill extraction.
Captures detailed logs at each stage of the pipeline for debugging and analysis.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class DebugLogger:
    """
    Comprehensive debug logger for extraction pipeline.
    Creates structured log files for each processing stage.
    """
    
    def __init__(self, output_dir: str, filename: str, enabled: bool = True):
        """
        Initialize debug logger.
        
        Args:
            output_dir: Base output directory
            filename: Name of the file being processed
            enabled: Whether logging is enabled
        """
        self.enabled = enabled
        if not enabled:
            return
        
        # Create debug directory structure
        base_name = Path(filename).stem
        self.debug_dir = Path(output_dir) / "debug_logs" / base_name
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata
        self.metadata = {
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
    
    def log_raw_ocr(self, ocr_text: str, confidence: float = None):
        """
        Log raw OCR output.
        
        Args:
            ocr_text: Raw OCR text
            confidence: Optional OCR confidence score
        """
        if not self.enabled:
            return
        
        log_file = self.debug_dir / "01_raw_ocr.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("RAW OCR OUTPUT\n")
            f.write("="*80 + "\n\n")
            
            if confidence is not None:
                f.write(f"Confidence Score: {confidence:.2f}%\n")
                f.write("-"*80 + "\n\n")
            
            f.write(f"Character Count: {len(ocr_text)}\n")
            f.write(f"Line Count: {len(ocr_text.splitlines())}\n")
            f.write("-"*80 + "\n\n")
            
            f.write("Full Text:\n")
            f.write("-"*80 + "\n")
            f.write(ocr_text)
            f.write("\n" + "="*80 + "\n")
        
        self.metadata["stages"]["raw_ocr"] = {
            "char_count": len(ocr_text),
            "line_count": len(ocr_text.splitlines()),
            "confidence": confidence
        }
    
    def log_cleaned_ocr(self, cleaned_text: str):
        """
        Log cleaned/preprocessed OCR text.
        
        Args:
            cleaned_text: Cleaned OCR text
        """
        if not self.enabled:
            return
        
        log_file = self.debug_dir / "02_cleaned_ocr.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("CLEANED OCR OUTPUT (Post-Processing)\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Character Count: {len(cleaned_text)}\n")
            f.write(f"Line Count: {len(cleaned_text.splitlines())}\n")
            f.write("-"*80 + "\n\n")
            
            f.write("Full Text:\n")
            f.write("-"*80 + "\n")
            f.write(cleaned_text)
            f.write("\n" + "="*80 + "\n")
        
        self.metadata["stages"]["cleaned_ocr"] = {
            "char_count": len(cleaned_text),
            "line_count": len(cleaned_text.splitlines())
        }
    
    def log_regex_extraction(self, regex_result: Dict):
        """
        Log regex extraction results.
        
        Args:
            regex_result: Dictionary of regex extraction results
        """
        if not self.enabled:
            return
        
        log_file = self.debug_dir / "03_regex_extraction.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "stage": "Regex Extraction",
                "timestamp": datetime.now().isoformat(),
                "results": regex_result,
                "fields_found": sum(1 for v in regex_result.values() if v is not None),
                "total_fields": len(regex_result)
            }, f, indent=2, ensure_ascii=False)
        
        self.metadata["stages"]["regex_extraction"] = {
            "fields_found": sum(1 for v in regex_result.values() if v is not None),
            "total_fields": len(regex_result)
        }
    
    def log_llm_prompt(self, system_message: str, user_prompt: str, model: str = "gpt-4o-mini"):
        """
        Log complete LLM prompt sent to OpenAI.
        
        Args:
            system_message: System message
            user_prompt: User prompt with OCR text
            model: Model name
        """
        if not self.enabled:
            return
        
        log_file = self.debug_dir / "04_llm_prompt.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LLM PROMPT SENT TO OPENAI\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Model: {model}\n")
            f.write(f"Temperature: 0\n")
            f.write(f"Response Format: JSON\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("-"*80 + "\n\n")
            
            f.write("SYSTEM MESSAGE:\n")
            f.write("-"*80 + "\n")
            f.write(system_message)
            f.write("\n\n" + "-"*80 + "\n\n")
            
            f.write("USER PROMPT:\n")
            f.write("-"*80 + "\n")
            f.write(user_prompt)
            f.write("\n\n" + "="*80 + "\n")
        
        self.metadata["stages"]["llm_prompt"] = {
            "model": model,
            "prompt_length": len(user_prompt),
            "timestamp": datetime.now().isoformat()
        }
    
    def log_llm_response(self, response_text: str, usage: Dict = None, model: str = None):
        """
        Log LLM response from OpenAI.
        
        Args:
            response_text: Raw response text (JSON)
            usage: Token usage statistics
            model: Model used
        """
        if not self.enabled:
            return
        
        log_file = self.debug_dir / "05_llm_response.json"
        
        # Parse response if it's JSON string
        try:
            response_data = json.loads(response_text) if isinstance(response_text, str) else response_text
        except:
            response_data = {"raw_text": response_text}
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "stage": "LLM Response",
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "usage": usage,
                "response": response_data
            }, f, indent=2, ensure_ascii=False)
        
        self.metadata["stages"]["llm_response"] = {
            "model": model,
            "usage": usage,
            "timestamp": datetime.now().isoformat()
        }
    
    def log_final_extraction(self, final_result: Dict):
        """
        Log final merged extraction results.
        
        Args:
            final_result: Final extraction dictionary
        """
        if not self.enabled:
            return
        
        log_file = self.debug_dir / "06_final_extraction.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "stage": "Final Extraction (Merged)",
                "timestamp": datetime.now().isoformat(),
                "results": final_result,
                "fields_found": sum(1 for v in final_result.values() if v is not None),
                "total_fields": len(final_result)
            }, f, indent=2, ensure_ascii=False)
        
        self.metadata["stages"]["final_extraction"] = {
            "fields_found": sum(1 for v in final_result.values() if v is not None),
            "total_fields": len(final_result)
        }
    
    def log_accuracy_evaluation(self, accuracy_data: Dict):
        """
        Log accuracy evaluation results.
        
        Args:
            accuracy_data: Accuracy evaluation dictionary
        """
        if not self.enabled:
            return
        
        log_file = self.debug_dir / "07_accuracy_evaluation.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "stage": "Accuracy Evaluation",
                "timestamp": datetime.now().isoformat(),
                "evaluation": accuracy_data
            }, f, indent=2, ensure_ascii=False)
        
        if accuracy_data:
            self.metadata["stages"]["accuracy_evaluation"] = {
                "overall_accuracy": accuracy_data.get("overall_accuracy"),
                "correct_fields": accuracy_data.get("correct_fields"),
                "total_fields": accuracy_data.get("total_fields")
            }
    
    def save_metadata(self):
        """Save processing metadata summary."""
        if not self.enabled:
            return
        
        metadata_file = self.debug_dir / "00_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def log_error(self, stage: str, error: Exception):
        """
        Log error that occurred during processing.
        
        Args:
            stage: Stage where error occurred
            error: Exception object
        """
        if not self.enabled:
            return
        
        error_file = self.debug_dir / "ERROR.txt"
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"ERROR in {stage}\n")
            f.write("="*80 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error Type: {type(error).__name__}\n")
            f.write(f"Error Message: {str(error)}\n")
            f.write("-"*80 + "\n\n")
            
            import traceback
            f.write("Traceback:\n")
            f.write(traceback.format_exc())
            f.write("\n" + "="*80 + "\n\n")
