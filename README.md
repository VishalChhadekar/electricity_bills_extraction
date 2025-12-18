# Electricity Bill Extraction Service

A backend-only service for extracting structured fields from Indian electricity bills using Google Cloud Vision OCR and OpenAI LLM.

## 🎯 Overview

This service processes electricity bills (PDF or image format) and extracts predefined fields with high accuracy using a hybrid approach:
- **Regex extraction** for structured fields (fast, deterministic)
- **LLM extraction** for unstructured/varying formats (flexible, intelligent)
- **Hybrid merge** where regex overrides LLM for reliability

## 📋 Features

- Supports PDF and image inputs (JPG, PNG)
- Multi-page PDF handling
- Image preprocessing (grayscale, denoise, threshold, deskew)
- Google Cloud Vision OCR integration
- OpenAI GPT-4o-mini for intelligent extraction
- Field-level accuracy evaluation
- Structured JSON output

## 🔑 Extracted Fields

The service extracts the following fields from electricity bills:

```json
{
  "consumer_name": "Full name of consumer",
  "consumer_number": "Consumer/account number",
  "meter_number": "Electricity meter number",
  "billing_period": "Billing period date range",
  "previous_reading_date": "Previous meter reading date",
  "current_reading_date": "Current meter reading date",
  "units_consumed": "Total units consumed (kWh)",
  "bill_amount": "Total bill amount",
  "due_date": "Payment due date",
  "address": "Consumer address",
  "discom": "Distribution company name"
}
```

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **OCR**: Google Cloud Vision API
- **LLM**: OpenAI (gpt-4o-mini)
- **Image Processing**: OpenCV
- **PDF Processing**: pdf2image

## 📁 Project Structure

```
bill-extractor/
├── input/                      # Place input bills here
│   └── sample_bill.pdf/jpg
├── expected/                   # Ground truth for evaluation
│   └── ground_truth.json
├── output/                     # Extraction results
│   ├── extracted.json
│   └── accuracy_report.json
├── src/
│   ├── main.py                # Main orchestration
│   ├── ocr/
│   │   └── google_ocr.py      # Google Vision integration
│   ├── preprocessing/
│   │   └── image_cleaner.py   # Image enhancement
│   ├── extraction/
│   │   ├── regex_extractor.py # Pattern-based extraction
│   │   └── llm_extractor.py   # LLM-based extraction
│   ├── evaluation/
│   │   └── accuracy.py        # Accuracy calculation
│   └── utils/
│       └── file_loader.py     # File I/O utilities
├── requirements.txt
└── README.md
```

## 🚀 Setup

### Prerequisites

1. **Python 3.10+** installed
2. **Google Cloud Vision API** credentials
3. **OpenAI API** key

### Installation

1. Clone or download this project

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:

**Windows (PowerShell):**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\your\service-account-key.json"
$env:OPENAI_API_KEY="your-openai-api-key"
```

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
export OPENAI_API_KEY="your-openai-api-key"
```

### Google Cloud Vision Setup

1. Create a Google Cloud project
2. Enable the Cloud Vision API
3. Create a service account and download the JSON key file
4. Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of this JSON file

### OpenAI Setup

1. Sign up at [OpenAI](https://platform.openai.com/)
2. Generate an API key
3. Set `OPENAI_API_KEY` environment variable

## ▶️ Usage

1. Place your electricity bill in the `input/` directory:
   - Name it `sample_bill.pdf` or `sample_bill.jpg`

2. (Optional) Create ground truth JSON in `expected/ground_truth.json` for accuracy evaluation

3. Run the extraction:
```bash
python src/main.py
```

4. Check results in `output/`:
   - `extracted.json` - Extracted fields
   - `accuracy_report.json` - Accuracy metrics (if ground truth provided)

## 📊 Processing Pipeline

1. **File Loading**: PDF → images or direct image load
2. **Preprocessing**: Grayscale → Denoise → Threshold → Deskew
3. **OCR**: Google Cloud Vision text extraction
4. **Regex Extraction**: Pattern-based field extraction
5. **LLM Extraction**: OpenAI GPT-4o-mini extraction
6. **Merge**: Regex overrides LLM (hybrid approach)
7. **Evaluation**: Compare with ground truth (if provided)

## 🎯 Accuracy Calculation

- **Normalization**: Case-insensitive, whitespace-trimmed comparison
- **Field-level**: Binary (correct/incorrect) for each field
- **Overall**: `(correct_fields / total_fields) × 100`

Example output:
```
Overall Accuracy: 90.91%
Correct Fields: 10/11

Field-Level Results:
consumer_name:
  Expected:  Rajesh Kumar
  Extracted: Rajesh Kumar
  Status:    ✓ CORRECT
```

## ⚙️ Configuration

### LLM Settings

In `src/extraction/llm_extractor.py`:
- **Model**: `gpt-4o-mini` (configurable)
- **Temperature**: `0` (deterministic)
- **Response format**: JSON only

### Regex Patterns

Patterns in `src/extraction/regex_extractor.py` can be customized for specific DISCOM formats.

## 🚫 Limitations

- **Single page processing**: Currently processes first page of multi-page PDFs
- **OCR quality dependent**: Accuracy depends on bill image quality
- **DISCOM variations**: Layout varies by distribution company
- **No database**: Results stored as JSON files only
- **No UI**: Command-line only

## 🔍 Troubleshooting

### "GOOGLE_APPLICATION_CREDENTIALS not set"
- Ensure environment variable points to valid service account JSON

### "OPENAI_API_KEY not set"
- Ensure environment variable contains valid OpenAI API key

### Low accuracy
- Check input image quality
- Verify ground truth JSON format
- Review OCR text in output for issues

### Import errors
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)

## 📝 Example Ground Truth Format

```json
{
  "consumer_name": "Rajesh Kumar",
  "consumer_number": "1234567890",
  "meter_number": "MET987654",
  "billing_period": "01-11-2024 to 30-11-2024",
  "previous_reading_date": "01-11-2024",
  "current_reading_date": "30-11-2024",
  "units_consumed": "250",
  "bill_amount": "1850.50",
  "due_date": "15-12-2024",
  "address": "123 Main Street, Mumbai, Maharashtra 400001",
  "discom": "MSEDCL"
}
```

## 🤝 Contributing

This is a production-quality codebase with:
- Clean, modular architecture
- Comprehensive comments
- Type hints
- Error handling

## 📄 License

This project is provided as-is for electricity bill extraction purposes.

---

**Built with ❤️ for accurate electricity bill data extraction**
