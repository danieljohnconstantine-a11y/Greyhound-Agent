"""
Test the complete ML pipeline with a single PDF to validate it works end-to-end.

This script:
1. Loads ONE PDF file from data/ folder
2. Matches it with CSV results  
3. Trains a minimal ML model
4. Makes predictions on the same PDF
5. Validates the complete pipeline

Usage:
    python test_single_pdf_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.parser import parse_race_form
from src.features import compute_features
from src.ml_predictor import GreyhoundMLPredictor
import pandas as pd
import pdfplumber
import glob

def test_single_pdf_pipeline():
    """Test complete pipeline with single PDF"""
    
    print("="*80)
    print("🧪 TESTING ML PIPELINE WITH SINGLE PDF")
    print("="*80)
    
    # Step 1: Find a PDF file
    pdf_files = glob.glob("data/*form.pdf")
    if not pdf_files:
        print("❌ No PDF files found in data/ folder!")
        return False
    
    test_pdf = pdf_files[0]
    print(f"\n📄 Using test PDF: {test_pdf}")
    
    # Step 2: Parse the PDF
    print("\n1️⃣  Parsing PDF...")
    try:
        with pdfplumber.open(test_pdf) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        df_dogs = parse_race_form(text)
        if df_dogs is None or df_dogs.empty:
            print("❌ PDF parsing returned empty dataframe!")
            return False
        
        print(f"✅ Parsed {len(df_dogs)} dogs from PDF")
        print(f"   Columns: {list(df_dogs.columns)}")
        
        # Check for required columns
        required_cols = ['Track', 'RaceNumber', 'Box']
        missing_cols = [col for col in required_cols if col not in df_dogs.columns]
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return False
        
        # Check for RaceDate
        if 'RaceDate' in df_dogs.columns:
            dates = df_dogs['RaceDate'].unique()
            print(f"✅ RaceDate found: {dates}")
        else:
            print("⚠️  No RaceDate column in parsed data!")
        
    except Exception as e:
        print(f"❌ Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Compute features
    print("\n2️⃣  Computing features...")
    try:
        df_dogs = compute_features(df_dogs)
        print(f"✅ Computed features for {len(df_dogs)} dogs")
        print(f"   Total columns: {len(df_dogs.columns)}")
    except Exception as e:
        print(f"❌ Error computing features: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Try to match with CSV results
    print("\n3️⃣  Matching with CSV results...")
    try:
        results_files = glob.glob("data/results_*.csv")
        print(f"   Found {len(results_files)} results CSV files")
        
        # Build results dictionary
        all_results = {}
        for results_file in results_files:
            filename = os.path.basename(results_file)
            csv_date = filename.replace('results_', '').replace('.csv', '')
            
            df_results = pd.read_csv(results_file)
            for _, row in df_results.iterrows():
                track = str(row.get('Track', ''))
                race_str = str(row.get('Race', row.get('RaceNumber', '0')))
                race_num = int(race_str.replace('R', '').replace('r', ''))
                winner_str = str(row.get('Winner', row.get('WinnerBox', '0')))
                winner_box = int(winner_str[0]) if winner_str and winner_str[0].isdigit() else 0
                
                if track and race_num and winner_box:
                    key = f"{csv_date}_{track.upper()}_R{race_num}"
                    all_results[key] = winner_box
        
        print(f"   Loaded {len(all_results)} race results")
        
        # Try to match races from our PDF
        matched_races = []
        for group_key, df_race in df_dogs.groupby(['Track', 'RaceNumber']):
            track, race_num = group_key
            race_date = df_race['RaceDate'].iloc[0] if 'RaceDate' in df_race.columns else 'UNKNOWN'
            
            # Try matching with date
            key = f"{race_date}_{track.upper()}_R{race_num}"
            if key in all_results:
                winner_box = all_results[key]
                print(f"✅ Matched: {key} -> winner box {winner_box}")
                matched_races.append((df_race, winner_box))
            else:
                # Try without date
                found = False
                for result_key in all_results.keys():
                    if result_key.endswith(f"_{track.upper()}_R{race_num}"):
                        winner_box = all_results[result_key]
                        print(f"✅ Matched (no date): {result_key} -> winner box {winner_box}")
                        matched_races.append((df_race, winner_box))
                        found = True
                        break
                
                if not found:
                    print(f"⚠️  No match: {key}")
                    print(f"   Available keys containing '{track}':")
                    matching_keys = [k for k in all_results.keys() if track.upper() in k.upper()]
                    for k in matching_keys[:5]:
                        print(f"     - {k}")
        
        if not matched_races:
            print("❌ No races could be matched with CSV results!")
            return False
        
        print(f"\n✅ Matched {len(matched_races)} races from this PDF")
        
    except Exception as e:
        print(f"❌ Error matching results: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Train minimal model
    print("\n4️⃣  Training minimal ML model...")
    try:
        race_data = [race for race, winner in matched_races]
        winners = [winner for race, winner in matched_races]
        
        if len(race_data) < 2:
            print(f"⚠️  Only {len(race_data)} race(s) - not enough for training")
            print("   Need at least 2 races to train a model")
            print("   Test passed - parsing and matching work correctly!")
            return True
        
        predictor = GreyhoundMLPredictor()
        metrics = predictor.train(race_data, winners)
        
        print(f"✅ Model trained successfully!")
        print(f"   Validation accuracy: {metrics['val_accuracy']*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Make predictions
    print("\n5️⃣  Making predictions...")
    try:
        test_race = race_data[0]
        confidences = predictor.predict_confidence(test_race)
        
        print(f"✅ Predictions generated!")
        print(f"   Confidence scores: {confidences}")
        
        # Find highest confidence
        max_confidence = confidences.max()
        predicted_box = confidences.idxmax()
        actual_winner = winners[0]
        
        print(f"\n📊 Prediction Result:")
        print(f"   Predicted winner: Box {predicted_box} ({max_confidence*100:.1f}% confidence)")
        print(f"   Actual winner: Box {actual_winner}")
        print(f"   Match: {'✅ CORRECT!' if predicted_box == actual_winner else '❌ INCORRECT'}")
        
    except Exception as e:
        print(f"❌ Error making predictions: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("✅ PIPELINE TEST COMPLETE - ALL STEPS WORKING!")
    print("="*80)
    return True

if __name__ == "__main__":
    success = test_single_pdf_pipeline()
    sys.exit(0 if success else 1)
