import pandas as pd
import numpy as np
import pdfplumber
import os
import logging
from datetime import datetime
from src.parser import parse_race_form
from src.features import compute_features  # ✅ Enhanced scoring logic

# ✅ Ensure outputs directory exists FIRST before logging setup
os.makedirs('outputs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file with error handling."""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        logger.warning(f"No text extracted from page {page_num} of {pdf_path}")
                except Exception as e:
                    logger.error(f"Error extracting text from page {page_num} of {pdf_path}: {e}")
        if not text.strip():
            logger.error(f"No text content extracted from {pdf_path}")
        return text
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return None

# 🚀 Start pipeline
logger.info("🚀 Starting Greyhound Analytics")
print("🚀 Starting Greyhound Analytics")

# ✅ Verify outputs directory exists (already created above for logging)
logger.info("Outputs directory ready")

# ✅ Find all PDFs in data folder
pdf_folder = "data"
if not os.path.exists(pdf_folder):
    logger.error(f"Data folder '{pdf_folder}' does not exist")
    print(f"❌ Data folder '{pdf_folder}' does not exist.")
    exit(1)

pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(pdf_folder, x)), reverse=True)

if not pdf_files:
    logger.error("No PDF files found in data folder")
    print("❌ No PDF files found in data folder.")
    exit(1)

logger.info(f"Found {len(pdf_files)} PDF files to process")
print(f"📁 Found {len(pdf_files)} PDF files to process")

all_dogs = []
parse_errors = []
parsing_stats = {
    'total_pdfs': len(pdf_files),
    'successful_pdfs': 0,
    'failed_pdfs': 0,
    'total_dogs': 0
}

# ✅ Process each PDF
for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_folder, pdf_file)
    logger.info(f"Processing PDF: {pdf_path}")
    print(f"📄 Processing: {pdf_path}")
    
    try:
        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text:
            logger.error(f"Failed to extract text from {pdf_file}")
            parse_errors.append(f"{pdf_file}: No text extracted")
            parsing_stats['failed_pdfs'] += 1
            continue
        
        df = parse_race_form(raw_text)
        
        if df is None or df.empty:
            logger.error(f"Parser returned empty DataFrame for {pdf_file}")
            parse_errors.append(f"{pdf_file}: No dogs parsed")
            parsing_stats['failed_pdfs'] += 1
            continue
        
        # ✅ Convert DLR to numeric to avoid type errors
        df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")
        
        # ✅ Apply enhanced scoring
        try:
            df = compute_features(df)
            parsing_stats['successful_pdfs'] += 1
            parsing_stats['total_dogs'] += len(df)
            all_dogs.append(df)
            logger.info(f"Successfully processed {pdf_file}: {len(df)} dogs")
        except Exception as e:
            logger.error(f"Feature computation failed for {pdf_file}: {e}")
            parse_errors.append(f"{pdf_file}: Feature computation error - {e}")
            parsing_stats['failed_pdfs'] += 1
            
    except Exception as e:
        logger.error(f"Unexpected error processing {pdf_file}: {e}")
        parse_errors.append(f"{pdf_file}: Unexpected error - {e}")
        parsing_stats['failed_pdfs'] += 1
        continue

# ✅ Check if any dogs were parsed
if not all_dogs:
    logger.error("No dogs were successfully parsed from any PDF")
    print("❌ No dogs were successfully parsed from any PDF")
    print(f"\nParsing errors: {len(parse_errors)}")
    for error in parse_errors:
        print(f"  - {error}")
    exit(1)

# ✅ Combine all dogs
combined_df = pd.concat(all_dogs, ignore_index=True)
logger.info(f"Total dogs parsed: {len(combined_df)}")
print(f"🐾 Total dogs parsed: {len(combined_df)}")

# ✅ Save full parsed form
try:
    combined_df.to_csv("outputs/todays_form.csv", index=False)
    logger.info("Saved parsed form → outputs/todays_form.csv")
    print("📄 Saved parsed form → outputs/todays_form.csv")
except Exception as e:
    logger.error(f"Failed to save todays_form.csv: {e}")
    print(f"❌ Failed to save todays_form.csv: {e}")

# ✅ Save ranked dogs
try:
    ranked = combined_df.sort_values(["Track", "RaceNumber", "FinalScore"], ascending=[True, True, False])
    ranked.to_csv("outputs/ranked.csv", index=False)
    logger.info("Saved ranked dogs → outputs/ranked.csv")
    print("📊 Saved ranked dogs → outputs/ranked.csv")
except Exception as e:
    logger.error(f"Failed to save ranked.csv: {e}")
    print(f"❌ Failed to save ranked.csv: {e}")

# ✅ Save top picks across all tracks
try:
    picks = ranked.groupby(["Track", "RaceNumber"]).head(1).reset_index(drop=True)
    picks = picks.sort_values("FinalScore", ascending=False)

    # Reorder columns
    priority_cols = ["Track", "RaceNumber", "Box", "DogName", "FinalScore", "PrizeMoney"]
    remaining_cols = [col for col in picks.columns if col not in priority_cols]
    ordered_cols = priority_cols + remaining_cols
    picks = picks[ordered_cols]

    picks.to_csv("outputs/picks.csv", index=False)
    logger.info("Saved top picks → outputs/picks.csv")
    print("🎯 Saved top picks → outputs/picks.csv")
except Exception as e:
    logger.error(f"Failed to save picks.csv: {e}")
    print(f"❌ Failed to save picks.csv: {e}")

# ✅ Display top picks
print("\n🏁 Top Picks Across All Tracks:")
try:
    for _, row in picks.iterrows():
        print(f"{row.Track} | Race {row.RaceNumber} | {row.DogName} | Score: {round(row.FinalScore, 3)}")
except Exception as e:
    logger.error(f"Error displaying top picks: {e}")

# ================================================================================
# VALIDATION REPORT
# ================================================================================
print("\n" + "=" * 80)
print("VALIDATION REPORT")
print("=" * 80)
logger.info("Starting validation report generation")

validation_issues = []

# 1. Check parsing statistics
print(f"\n📊 PARSING STATISTICS:")
print(f"  Total PDFs found: {parsing_stats['total_pdfs']}")
print(f"  Successfully parsed: {parsing_stats['successful_pdfs']}")
print(f"  Failed to parse: {parsing_stats['failed_pdfs']}")
print(f"  Total dogs extracted: {parsing_stats['total_dogs']}")

if parse_errors:
    print(f"\n⚠️  PARSE ERRORS ({len(parse_errors)}):")
    for error in parse_errors:
        print(f"  - {error}")
    validation_issues.extend(parse_errors)

# 2. Check for missing required columns
print(f"\n📋 COLUMN VALIDATION:")
required_cols = ["DogName", "Track", "RaceNumber", "Box", "FinalScore", "PrizeMoney"]
missing_cols = [col for col in required_cols if col not in combined_df.columns]
if missing_cols:
    msg = f"Missing required columns: {missing_cols}"
    print(f"  ❌ {msg}")
    validation_issues.append(msg)
    logger.error(msg)
else:
    print(f"  ✅ All required columns present")

# 3. Check for missing data in critical fields
print(f"\n🔍 MISSING DATA CHECK:")
for col in required_cols:
    if col in combined_df.columns:
        missing_count = combined_df[col].isna().sum()
        if missing_count > 0:
            msg = f"{col}: {missing_count} missing values ({missing_count/len(combined_df)*100:.1f}%)"
            print(f"  ⚠️  {msg}")
            validation_issues.append(msg)
            logger.warning(msg)
        else:
            print(f"  ✅ {col}: No missing values")

# 4. Check for duplicate dog entries (same dog in same race)
print(f"\n🔎 DUPLICATE CHECK:")
race_dog_combos = combined_df.groupby(['Track', 'RaceNumber', 'Box']).size()
duplicates = race_dog_combos[race_dog_combos > 1]
if len(duplicates) > 0:
    msg = f"Found {len(duplicates)} duplicate race/box combinations"
    print(f"  ⚠️  {msg}")
    for (track, race, box), count in duplicates.items():
        dup_msg = f"Track={track}, Race={race}, Box={box}: {count} entries"
        print(f"     - {dup_msg}")
        validation_issues.append(dup_msg)
    logger.warning(msg)
else:
    print(f"  ✅ No duplicate race/box combinations found")

# 5. Check for anomalies - all dogs with same values for columns
print(f"\n⚙️  ANOMALY DETECTION:")
check_cols = ["BestTimeSec", "SectionalSec", "Weight"]
for col in check_cols:
    if col in combined_df.columns:
        unique_vals = combined_df[col].nunique()
        total_vals = len(combined_df[col].dropna())
        if unique_vals == 1 and total_vals > 1:
            msg = f"{col}: All {total_vals} dogs have the same value ({combined_df[col].iloc[0]})"
            print(f"  ⚠️  {msg}")
            validation_issues.append(msg)
            logger.warning(msg)
        elif unique_vals < 5 and total_vals > 20:
            msg = f"{col}: Only {unique_vals} unique values for {total_vals} dogs (might be placeholder data)"
            print(f"  ⚠️  {msg}")
            validation_issues.append(msg)
            logger.warning(msg)
        else:
            print(f"  ✅ {col}: {unique_vals} unique values for {total_vals} dogs")

# 6. Verify output files exist
print(f"\n📁 OUTPUT FILE VERIFICATION:")
output_files = ["outputs/todays_form.csv", "outputs/ranked.csv", "outputs/picks.csv"]
for filepath in output_files:
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"  ✅ {filepath} exists ({size} bytes)")
        logger.info(f"Output file verified: {filepath} ({size} bytes)")
    else:
        msg = f"{filepath} was not created"
        print(f"  ❌ {msg}")
        validation_issues.append(msg)
        logger.error(msg)

# 7. Summary
print(f"\n" + "=" * 80)
if validation_issues:
    print(f"⚠️  VALIDATION COMPLETE: {len(validation_issues)} issue(s) found")
    logger.warning(f"Validation complete with {len(validation_issues)} issues")
else:
    print(f"✅ VALIDATION COMPLETE: No issues found")
    logger.info("Validation complete - no issues found")
print("=" * 80)

# Save validation report to file
try:
    with open("outputs/validation_report.txt", "w") as f:
        f.write("GREYHOUND ANALYTICS VALIDATION REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("PARSING STATISTICS:\n")
        f.write(f"  Total PDFs found: {parsing_stats['total_pdfs']}\n")
        f.write(f"  Successfully parsed: {parsing_stats['successful_pdfs']}\n")
        f.write(f"  Failed to parse: {parsing_stats['failed_pdfs']}\n")
        f.write(f"  Total dogs extracted: {parsing_stats['total_dogs']}\n\n")
        
        if parse_errors:
            f.write(f"PARSE ERRORS ({len(parse_errors)}):\n")
            for error in parse_errors:
                f.write(f"  - {error}\n")
            f.write("\n")
        
        if validation_issues:
            f.write(f"VALIDATION ISSUES ({len(validation_issues)}):\n")
            for issue in validation_issues:
                f.write(f"  - {issue}\n")
        else:
            f.write("✅ No validation issues found\n")
        
        f.write("\n" + "=" * 80 + "\n")
    
    print(f"\n📝 Validation report saved to outputs/validation_report.txt")
    logger.info("Validation report saved to outputs/validation_report.txt")
except Exception as e:
    logger.error(f"Failed to save validation report: {e}")
    print(f"❌ Failed to save validation report: {e}")

print("\n📌 Press Enter to exit...")
input()
