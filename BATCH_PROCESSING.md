# Batch Processing Guide

## 🎯 Overview

The tool now supports **batch processing** - it can process **all files** in the `/input` directory at once, regardless of filename!

## ✅ Supported Formats

- **PDF** (`.pdf`)
- **JPG** (`.jpg`, `.jpeg`)
- **PNG** (`.png`)

Case-insensitive (`.PDF`, `.JPG`, etc. also work)

---

## 🚀 How to Use

### 1. Add Your Files

Simply place any number of bills in the `/input` directory:

```
input/
├── bill_january.pdf
├── bill_february.jpg
├── customer_123.png
├── electricity_bill_march.pdf
└── any_other_name.jpg
```

**No specific naming required!** Use any filenames you want.

### 2. Run Batch Processing

```bash
python src/main.py
```

Or use the convenience script:

```bash
python run_batch.py
```

### 3. Check Results

Each file gets its own output files:

```
output/
├── bill_january_extracted.json
├── bill_january_accuracy_report.json
├── bill_february_extracted.json
├── bill_february_accuracy_report.json
├── customer_123_extracted.json
├── customer_123_accuracy_report.json
└── ...
```

---

## 📊 Output Format

### Filename Pattern

- **Input:** `input/my_bill.pdf`
- **Output:** `output/my_bill_extracted.json`
- **Accuracy:** `output/my_bill_accuracy_report.json`

### Summary Report

At the end, you'll see a summary:

```
============================================================
PROCESSING SUMMARY
============================================================
Total files processed: 3
============================================================

1. bill_january.pdf
   Accuracy: 90.91% (10/11 fields)

2. bill_february.jpg
   Accuracy: 81.82% (9/11 fields)

3. customer_123.png
   Status: ✓ Processed (no ground truth)

============================================================
All processing complete!
Results saved to: output/
============================================================
```

---

## 🔍 Ground Truth Handling

### Single Ground Truth (Current)

Currently uses `expected/ground_truth.json` for **all files**.

- If present: Calculates accuracy for each file
- If missing: Skips accuracy evaluation

### Multiple Ground Truths (Future Enhancement)

You could extend this to support per-file ground truth:

```
expected/
├── bill_january_ground_truth.json
├── bill_february_ground_truth.json
└── customer_123_ground_truth.json
```

---

## 💡 Usage Examples

### Example 1: Process Single File

```bash
# Add one file
input/my_bill.pdf

# Run
python src/main.py

# Output
output/my_bill_extracted.json
output/my_bill_accuracy_report.json
```

### Example 2: Process Multiple Files

```bash
# Add multiple files
input/jan.pdf
input/feb.pdf
input/mar.pdf

# Run
python src/main.py

# Output
output/jan_extracted.json
output/jan_accuracy_report.json
output/feb_extracted.json
output/feb_accuracy_report.json
output/mar_extracted.json
output/mar_accuracy_report.json
```

### Example 3: Mixed Formats

```bash
# Add different formats
input/bill1.pdf
input/bill2.jpg
input/bill3.png

# All processed automatically!
python src/main.py
```

---

## ⚙️ Configuration

### Verbose Mode

To see detailed logs for each file, edit `src/main.py`:

```python
result = process_bill(
    str(input_path),
    str(ground_truth_path) if ground_truth_path else None,
    verbose=True  # Change to True for detailed logs
)
```

Or use the verbose script:

```bash
python run_verbose.py  # Only processes first file with verbose logs
```

---

## 🎯 Best Practices

### Organizing Files

Use descriptive filenames:
```
input/
├── 2024_01_customer_A.pdf
├── 2024_02_customer_A.pdf
├── 2024_01_customer_B.jpg
└── 2024_02_customer_B.jpg
```

### Batch Size

- **Small batches (1-10 files):** Fast, easy to review
- **Large batches (100+ files):** Consider running overnight
- **API limits:** Monitor Google Vision and OpenAI quotas

### Error Handling

If one file fails, others continue processing:

```
1. good_bill.pdf
   Accuracy: 90.91% (10/11 fields)

2. corrupted_bill.pdf
   Status: ❌ Failed - Unable to decode image

3. another_bill.jpg
   Accuracy: 81.82% (9/11 fields)
```

---

## 🔧 Troubleshooting

### "No input files found"

**Problem:** Empty input directory

**Solution:**
```bash
# Check directory
ls input/

# Add files
cp /path/to/bills/*.pdf input/
```

### Files Not Processing

**Problem:** Unsupported format

**Solution:** Convert to PDF, JPG, or PNG:
```bash
# Convert TIFF to PDF (example)
convert bill.tiff bill.pdf
```

### Out of Memory

**Problem:** Too many large files

**Solution:** Process in smaller batches:
```bash
# Move files to temp directory
mkdir temp_input
mv input/*.pdf temp_input/

# Process in batches of 10
mv temp_input/bill_[0-9].pdf input/
python src/main.py

mv temp_input/bill_1[0-9].pdf input/
python src/main.py
```

---

## 💰 Cost Estimation

### Per File Costs

- **Google Vision:** ~$0.0015 per bill (after free tier)
- **OpenAI GPT-4o-mini:** ~$0.0001 per bill
- **Total:** ~$0.0016 per bill

### Batch Costs

- **10 files:** ~$0.016
- **100 files:** ~$0.16
- **1,000 files:** ~$1.60

Very affordable for most use cases!

---

## ✨ Summary

**Before:** Required specific filename `sample_bill.*`

**Now:** Processes **any filename** in `/input` directory!

**Benefits:**
- ✅ No renaming required
- ✅ Batch processing support
- ✅ Flexible file organization
- ✅ Individual output files per input
- ✅ Summary report at the end

**Happy batch processing! 🚀**
