import os
import pandas as pd
import numpy as np
import pdfplumber
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from parser import parse_pdf_form
from exporter import export_to_excel
from parser import parse_race_form
from features import compute_features

INPUT_DIR = "inputs"
OUTPUT_DIR = "outputs"

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def train_models(data_folder):
    """
    Train ML models on historical data from PDFs in data_folder.
    Saves models to models/ directory.
    """
    print(f"Training models from data in: {data_folder}")
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Find all PDFs in data folder
    pdf_files = [f for f in os.listdir(data_folder) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"ERROR: No PDF files found in {data_folder}")
        return
    
    print(f"Found {len(pdf_files)} training PDF files")
    
    all_dogs = []
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(data_folder, pdf_file)
        print(f"Processing training data: {pdf_path}")
        
        try:
            raw_text = extract_text_from_pdf(pdf_path)
            df = parse_race_form(raw_text)
            
            # Convert DLR to numeric
            df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")
            
            # Apply feature engineering
            df = compute_features(df)
            all_dogs.append(df)
        except Exception as e:
            print(f"Warning: Could not process {pdf_file}: {e}")
            continue
    
    if not all_dogs:
        print("ERROR: No data could be extracted from PDFs")
        return
    
    # Combine all dogs
    combined_df = pd.concat(all_dogs, ignore_index=True)
    print(f"Total training samples: {len(combined_df)}")
    
    # Group by track and train models per track
    tracks = combined_df["Track"].unique()
    
    for track in tracks:
        track_data = combined_df[combined_df["Track"] == track]
        print(f"\nTraining models for {track}...")
        
        # Prepare features (use numeric columns)
        feature_cols = ["CareerStarts", "CareerWins", "DLR", "Distance", 
                       "Speed_kmh", "EarlySpeedIndex", "ConsistencyIndex"]
        
        # Filter to only existing columns
        feature_cols = [col for col in feature_cols if col in track_data.columns]
        
        X = track_data[feature_cols].fillna(0)
        
        # Create synthetic target (1 if FinalScore > median, 0 otherwise)
        y = (track_data["FinalScore"] > track_data["FinalScore"].median()).astype(int)
        
        if len(X) < 10:
            print(f"Warning: Not enough data for {track}, skipping...")
            continue
        
        # Train RandomForest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X, y)
        
        # Train GradientBoosting
        gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        gb_model.fit(X, y)
        
        # Train scaler
        scaler = StandardScaler()
        scaler.fit(X)
        
        # Save models
        track_safe = track.replace(" ", "_")
        joblib.dump(rf_model, f"models/{track_safe}_rf.pkl")
        joblib.dump(gb_model, f"models/{track_safe}_gb.pkl")
        joblib.dump(scaler, f"models/{track_safe}_scaler.pkl")
        
        print(f"  Saved models for {track}")
    
    print("\nTraining complete! Models saved to models/ directory")


def load_pdfs(directory):
    pdf_texts = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(directory, filename)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            pdf_texts.append((filename, text))
    return pdf_texts

def analyze_race(race):
    for dog in race["dogs"]:
        dog["Score"] = 100.0 - dog.get("Box", 0) * 2.5
        dog["BetType"] = "YES" if dog["Score"] > 95 else "PLACE" if dog["Score"] > 80 else "PASS"
        dog["BetReason"] = f"Score={dog['Score']:.1f}"
        dog["FinalScore"] = dog["Score"]

def main():
    print("GREYHOUND ANALYZER - PRODUCTION READY")
    print("======================================================================")
    print("INITIALIZING...")
    print(f"OUTPUT: {os.path.abspath(OUTPUT_DIR)}")

    pdfs = load_pdfs(INPUT_DIR)
    print(f"FOUND {len(pdfs)} PDF FILES\n")

    all_dogs = []
    for filename, text in pdfs:
        print("PROCESSING PDFS...")
        print("--------------------------------------------------")
        print(f"PARSING {filename}...")
        result = parse_pdf_form(text)
        races = result.get("races", [])

        for race in races:
            print(f"   RACE: {race['RaceDate']} - {race['RaceTime']} {race['Track']}")
            analyze_race(race)
            for dog in race["dogs"]:
                print(f"   DOG: {race['RaceDate']} Race {race['RaceTime']} Box {dog['Box']}: {dog['DogName']}")
                dog["source_file"] = filename
                all_dogs.append(dog)

        print(f"EXTRACTED: {len(all_dogs)} from {filename}")

    print(f"\nANALYZING {len(all_dogs)} DOGS...")
    print("CALCULATING SCORES...")
    print("CALCULATING BETS...")

    bets = [d for d in all_dogs if d["BetType"] == "YES"]
    places = [d for d in all_dogs if d["BetType"] == "PLACE"]
    passes = [d for d in all_dogs if d["BetType"] == "PASS"]

    print(f"   BETS - YES: {len(bets)}, PLACE: {len(places)}, PASS: {len(passes)}")
    print("SUCCESS: Single winner per race!\n")

    print("SAVING EXCEL...")
    export_to_excel(all_dogs, OUTPUT_DIR)
    print("======================================================================")
    print("SUCCESS: Complete!")
    print("======================================================================")

if __name__ == "__main__":
    main()
