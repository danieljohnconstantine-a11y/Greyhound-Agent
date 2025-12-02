import pandas as pd
import numpy as np
import pdfplumber
import os
import logging
from src.parser import parse_race_form
from src.features import compute_features  # ✅ Enhanced scoring logic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logging.error(f"❌ Error extracting text from {pdf_path}: {e}")
        raise
    return text

# 🚀 Start pipeline
print("🚀 Starting Greyhound Analytics")

# ✅ Ensure outputs directory exists
output_dir = "outputs"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    logging.info(f"✅ Created outputs directory: {output_dir}")

# ✅ Find all PDFs in data folder
pdf_folder = "data"
pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(pdf_folder, x)), reverse=True)

if not pdf_files:
    print("❌ No PDF files found in data folder.")
    exit()

all_dogs = []

# ✅ Process each PDF
for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_folder, pdf_file)
    print(f"📄 Processing: {pdf_path}")
    
    try:
        raw_text = extract_text_from_pdf(pdf_path)
        df = parse_race_form(raw_text)
        
        if len(df) == 0:
            logging.warning(f"⚠️ No dogs parsed from {pdf_file} - skipping")
            continue

        # ✅ Convert DLR to numeric to avoid type errors
        df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")

        # ✅ Apply enhanced scoring
        df = compute_features(df)
        all_dogs.append(df)
        logging.info(f"✅ Successfully processed {pdf_file}: {len(df)} dogs")
    except Exception as e:
        logging.error(f"❌ Error processing {pdf_file}: {e}")
        # Continue processing other PDFs rather than crashing

# Check if we have any dogs
if not all_dogs:
    logging.error("❌ No dogs were parsed from any PDF files. Check PDF format and parsing logic.")
    print("❌ No valid data to process. Exiting.")
    input()
    exit(1)

# ✅ Combine all dogs
combined_df = pd.concat(all_dogs, ignore_index=True)
print(f"🐾 Total dogs parsed: {len(combined_df)}")

# ✅ Remove duplicate dogs (same dog in same race)
# Identify duplicates based on Track, RaceNumber, and DogName
initial_count = len(combined_df)
combined_df = combined_df.drop_duplicates(subset=["Track", "RaceNumber", "DogName"], keep="first")
duplicates_removed = initial_count - len(combined_df)

if duplicates_removed > 0:
    logging.warning(f"⚠️ Removed {duplicates_removed} duplicate dog entries")
    print(f"⚠️ Removed {duplicates_removed} duplicates")

print(f"🐾 Unique dogs after deduplication: {len(combined_df)}")

# ✅ Save full parsed form
combined_df.to_csv("outputs/todays_form.csv", index=False)
print("📄 Saved parsed form → outputs/todays_form.csv")

# ✅ Save ranked dogs
ranked = combined_df.sort_values(["Track", "RaceNumber", "FinalScore"], ascending=[True, True, False])
ranked.to_csv("outputs/ranked.csv", index=False)
print("📊 Saved ranked dogs → outputs/ranked.csv")

# ✅ Save top picks across all tracks
picks = ranked.groupby(["Track", "RaceNumber"]).head(1).reset_index(drop=True)
picks = picks.sort_values("FinalScore", ascending=False)

# Reorder columns
priority_cols = ["Track", "RaceNumber", "Box", "DogName", "FinalScore", "PrizeMoney"]
remaining_cols = [col for col in picks.columns if col not in priority_cols]
ordered_cols = priority_cols + remaining_cols
picks = picks[ordered_cols]

picks.to_csv("outputs/picks.csv", index=False)
print("🎯 Saved top picks → outputs/picks.csv")

# ✅ Display top picks
print("\n🏁 Top Picks Across All Tracks:")
for _, row in picks.iterrows():
    print(f"{row.Track} | Race {row.RaceNumber} | {row.DogName} | Score: {round(row.FinalScore, 3)}")

print("\n📌 Press Enter to exit...")
input()
