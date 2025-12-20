import pandas as pd
import numpy as np
import pdfplumber
import os
import sys
import glob
import logging
from src.parser import parse_race_form
from src.features import compute_features  # ✅ Enhanced scoring logic
from src.excel_export import create_color_coded_outputs  # ✅ Excel color-coding
from src.bet_worthy import identify_bet_worthy_races, print_bet_worthy_summary, get_selective_picks, get_lock_picks
from src.excel_formatter import export_to_excel_with_formatting

# Ensure outputs directory exists before configuring logging
os.makedirs('outputs', exist_ok=True)

# Configure logging with UTF-8 encoding for Windows console compatibility
log_file_handler = logging.FileHandler('outputs/greyhound_analytics.log', encoding='utf-8')
log_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# StreamHandler for console - use UTF-8 encoding to handle emoji characters
log_console_handler = logging.StreamHandler()
log_console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# Set UTF-8 encoding on stdout to handle Unicode characters on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[log_file_handler, log_console_handler]
)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# 🚀 Start pipeline
logger.info("🚀 Starting Greyhound Analytics - Ultra-Selective Betting v3.0")
print("🚀 Starting Greyhound Analytics - Ultra-Selective Betting v3.0")

# ✅ Determine PDF files to process
# If command-line arguments provided, use those files
# Otherwise, use all PDFs in the data folder
if len(sys.argv) > 1:
    # Command-line arguments provided (e.g., data_predictions\*.pdf)
    pdf_paths = []
    for arg in sys.argv[1:]:
        # Handle wildcards
        if '*' in arg or '?' in arg:
            pdf_paths.extend(glob.glob(arg))
        else:
            pdf_paths.append(arg)
    
    # Filter to only .pdf files and verify they exist
    pdf_paths = [p for p in pdf_paths if p.lower().endswith('.pdf') and os.path.exists(p)]
    
    if not pdf_paths:
        print("❌ No valid PDF files found from command-line arguments.")
        print(f"   Arguments: {sys.argv[1:]}")
        exit()
    
    print(f"📁 Processing {len(pdf_paths)} PDF file(s) from command line")
else:
    # No arguments - use default data folder
    pdf_folder = "data"
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(pdf_folder, x)), reverse=True)
    pdf_paths = [os.path.join(pdf_folder, f) for f in pdf_files]
    
    if not pdf_paths:
        print("❌ No PDF files found in data folder.")
        exit()
    
    print(f"📁 Processing {len(pdf_paths)} PDF file(s) from data/ folder")

all_dogs = []

# ✅ Process each PDF
for pdf_path in pdf_paths:
    print(f"📄 Processing: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)
    df = parse_race_form(raw_text)

    # ✅ Convert DLR to numeric to avoid type errors
    df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")

    # ✅ Apply enhanced scoring
    df = compute_features(df)
    all_dogs.append(df)

# ✅ Combine all dogs
combined_df = pd.concat(all_dogs, ignore_index=True)
print(f"🐾 Total dogs parsed: {len(combined_df)}")

# ✅ Save full parsed form as CSV (for backward compatibility)
combined_df.to_csv("outputs/todays_form.csv", index=False)
print("📄 Saved parsed form → outputs/todays_form.csv")

# 🎯 Identify bet-worthy races using SELECTIVE BETTING (TIER1 + TIER2 only)
print("\n" + "="*80)
print("🎯 SELECTIVE BETTING ANALYSIS")
print("="*80)
bet_worthy_races = identify_bet_worthy_races(combined_df, selective_mode=True)
print_bet_worthy_summary(bet_worthy_races)

# 📊 Save full parsed form as Excel with color highlighting for bet-worthy races
excel_output_path = "outputs/todays_form_color.xlsx"
export_to_excel_with_formatting(combined_df, bet_worthy_races, excel_output_path)

# ✅ Save ranked dogs
ranked = combined_df.sort_values(["Track", "RaceNumber", "FinalScore"], ascending=[True, True, False])
ranked.to_csv("outputs/ranked.csv", index=False)
print("📊 Saved ranked dogs → outputs/ranked.csv")

# ✅ Save ALL top picks across all tracks
picks = ranked.groupby(["Track", "RaceNumber"]).head(1).reset_index(drop=True)
picks = picks.sort_values("FinalScore", ascending=False)

# Reorder columns
priority_cols = ["Track", "RaceNumber", "Box", "DogName", "FinalScore", "PrizeMoney"]
remaining_cols = [col for col in picks.columns if col not in priority_cols]
ordered_cols = priority_cols + remaining_cols
picks = picks[ordered_cols]

picks.to_csv("outputs/picks.csv", index=False)
print("🎯 Saved all picks → outputs/picks.csv")

# ✅ Save SELECTIVE picks (TIER1 + TIER2 only) - Higher Win Rate Strategy
selective_picks = get_selective_picks(combined_df, bet_worthy_races)
if len(selective_picks) > 0:
    # Reorder columns for selective picks
    selective_priority = ["Track", "RaceNumber", "Box", "DogName", "FinalScore", "Tier", "ExpectedWinRate", "ScoreMargin"]
    selective_remaining = [col for col in selective_picks.columns if col not in selective_priority]
    selective_ordered = [c for c in selective_priority if c in selective_picks.columns] + selective_remaining
    selective_picks = selective_picks[selective_ordered]
    selective_picks.to_csv("outputs/selective_picks.csv", index=False)
    print(f"🔥 Saved selective picks → outputs/selective_picks.csv ({len(selective_picks)} races)")
    
    # Calculate expected stats
    tier0_count = len(selective_picks[selective_picks['Tier'] == 'TIER0'])
    tier1_count = len(selective_picks[selective_picks['Tier'] == 'TIER1'])
    tier2_count = len(selective_picks[selective_picks['Tier'] == 'TIER2'])
    expected_wins = tier0_count * 0.375 + tier1_count * 0.30 + tier2_count * 0.25
    print(f"   Expected wins: {expected_wins:.1f} ({expected_wins/len(selective_picks)*100:.1f}% win rate)")
else:
    print("⚠️  No selective picks meeting TIER0/TIER1/TIER2 criteria found")

# ✅ Save LOCK picks (TIER0 only) - Highest Confidence Bets
lock_picks = get_lock_picks(combined_df, bet_worthy_races)
if len(lock_picks) > 0:
    # Reorder columns for lock picks
    lock_priority = ["Track", "RaceNumber", "Box", "DogName", "FinalScore", "Tier", "LockReason", "ExpectedWinRate"]
    lock_remaining = [col for col in lock_picks.columns if col not in lock_priority]
    lock_ordered = [c for c in lock_priority if c in lock_picks.columns] + lock_remaining
    lock_picks = lock_picks[lock_ordered]
    lock_picks.to_csv("outputs/lock_picks.csv", index=False)
    print(f"🔒 Saved LOCK picks → outputs/lock_picks.csv ({len(lock_picks)} LOCK races)")
    print(f"   Expected wins from LOCKs: {len(lock_picks) * 0.375:.1f} ({37.5}% win rate)")
else:
    print("ℹ️  No LOCK picks (TIER0) today - criteria: Score ≥50, Margin ≥15%, Box 1 or 8, 30+ starts")

# ✅ Create color-coded Excel outputs
print("\n🎨 Creating color-coded Excel files...")
create_color_coded_outputs(combined_df)

# ✅ Display SELECTIVE picks (Recommended Bets)
print("\n" + "="*80)
print("🏁 RECOMMENDED BETS (TIER0 + TIER1 + TIER2)")
print("="*80)

# First show LOCK picks
if len(lock_picks) > 0:
    print("\n🔒 LOCK OF THE DAY (Highest Confidence):")
    for _, row in lock_picks.iterrows():
        print(f"   🔒 {row.Track} | Race {row.RaceNumber} | Box {row.Box} | {row.DogName} | Score: {round(row.FinalScore, 2)} | {row.get('LockReason', '')}")

# Then show other selective picks
if len(selective_picks) > 0:
    print("\n🎯 SELECTIVE PICKS (High Confidence):")
    for _, row in selective_picks.iterrows():
        if row.get('Tier') == 'TIER0':
            continue  # Already shown above
        tier_emoji = "🔥" if row.get('Tier') == 'TIER1' else "✅"
        print(f"   {tier_emoji} {row.Track} | Race {row.RaceNumber} | Box {row.Box} | {row.DogName} | Score: {round(row.FinalScore, 2)} | {row.get('Tier', 'N/A')}")
else:
    print("No races meeting selective betting criteria today.")

# ✅ Display ALL picks for reference
print("\n📋 All Top Picks (for reference):")
for _, row in picks.head(20).iterrows():
    # Check if this pick is in selective bets
    is_selective = False
    for _, sr in selective_picks.iterrows() if len(selective_picks) > 0 else []:
        if sr['Track'] == row.Track and sr['RaceNumber'] == row.RaceNumber:
            is_selective = True
            break
    marker = "⭐" if is_selective else "  "
    print(f"{marker} {row.Track} | Race {row.RaceNumber} | {row.DogName} | Score: {round(row.FinalScore, 3)}")

logger.info("✅ Greyhound Analytics pipeline completed successfully")
print("\n✅ Pipeline complete! Check outputs/selective_picks.csv for recommended bets.")
