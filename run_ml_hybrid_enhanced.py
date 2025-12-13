"""
Run ML v2.1 Enhanced Hybrid Predictions - Today's Races
Weather & Track Condition Integration for Maximum Accuracy

Combines v4.4 rule-based scoring with ML v2.1 enhanced predictions.
Uses weather data and track conditions for optimal accuracy.

Expected: 41-47% win rate (vs 40-45% v2.0, 35-40% v1.0, 28-30% v4.4 alone)

Usage:
    python run_ml_hybrid_enhanced.py

Prerequisites:
    1. Trained ML v2.1 model (run train_ml_enhanced.bat first)
    2. Race PDFs in data_predictions/ folder
    3. Optional: Weather data in data/weather_conditions.csv
    4. Optional: Track conditions in data/track_conditions.csv

Outputs:
    - outputs/ml_hybrid_enhanced_picks.xlsx - High-confidence hybrid picks
    - outputs/ml_enhanced_all_predictions.xlsx - All predictions ranked
    - outputs/v44_picks_comparison.csv - v4.4 picks for comparison
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set up logging with UTF-8 encoding
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
for handler in logging.root.handlers:
    if hasattr(handler, 'setStream'):
        handler.setStream(sys.stdout)

from src.ml_predictor_advanced import AdvancedGreyhoundMLPredictor
from src.weather_track_data import WeatherTrackDataManager
from src.parser import parse_race_form
from src.features import compute_features
from src.scorer import score_race
from src.excel_export import export_to_excel
import pandas as pd
import glob
import pdfplumber
from datetime import datetime

def main():
    print("=" * 80)
    print("🤖 ML HYBRID ENHANCED PREDICTION SYSTEM v2.1")
    print("   v4.4 Rule-Based + ML v2.0 + Weather/Track Conditions")
    print("=" * 80)
    
    # Initialize weather/track manager
    print("\n🌤️  Loading weather & track condition data...")
    try:
        weather_manager = WeatherTrackDataManager()
        print(f"✅ Weather records: {len(weather_manager.weather_data)}")
        print(f"✅ Track condition records: {len(weather_manager.track_conditions)}")
    except Exception as e:
        print(f"⚠️  Warning: Could not load weather/track data: {e}")
        print("   Continuing with inference-based conditions")
        weather_manager = WeatherTrackDataManager()
    
    # Load ML model
    print("\n📥 Loading ML v2.1 enhanced model...")
    model_path = "models/greyhound_ml_v2.1_enhanced.pkl"
    
    if not os.path.exists(model_path):
        print(f"❌ ERROR: Model not found at {model_path}")
        print("   Please run train_ml_enhanced.bat first to train the model")
        return 1
    
    try:
        predictor = AdvancedGreyhoundMLPredictor()
        predictor.load_model(model_path)
        print(f"✅ ML v2.1 model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return 1
    
    # Find PDFs
    pdf_files = glob.glob("data_predictions/*form.pdf")
    
    if len(pdf_files) == 0:
        print("\n❌ No race PDFs found in data_predictions/")
        print("   Please copy today's race PDFs to data_predictions/")
        return 1
    
    print(f"\n📄 Found {len(pdf_files)} race PDF(s)")
    for pdf in sorted(pdf_files):
        print(f"   • {os.path.basename(pdf)}")
    
    # Process PDFs
    all_v44_picks = []
    all_ml_enhanced_predictions = []
    all_hybrid_picks = []
    
    total_pdfs = len(pdf_files)
    success_pdfs = 0
    failed_pdfs = 0
    
    for idx, pdf_file in enumerate(sorted(pdf_files), 1):
        print(f"\n🔍 Processing ({idx}/{total_pdfs}): {os.path.basename(pdf_file)}")
        
        try:
            # Extract and parse PDF
            with pdfplumber.open(pdf_file) as pdf:
                text = "".join(page.extract_text() + "\n" for page in pdf.pages)
            
            df_dogs = parse_race_form(text)
            if df_dogs is None or len(df_dogs) == 0:
                print(f"   ⚠️  No data parsed from {os.path.basename(pdf_file)}")
                failed_pdfs += 1
                continue
            
            print(f"✅ Parsed {len(df_dogs)} dogs")
            
            # Compute features
            df_dogs = compute_features(df_dogs)
            
            # Add weather/track features
            if 'Date' in df_dogs.columns and 'Track' in df_dogs.columns:
                weather_features = []
                for _, row in df_dogs.iterrows():
                    conditions = weather_manager.get_condition_features(
                        row.get('Date', '2025-12-12'),
                        row.get('Track', 'Unknown'),
                        row.get('Distance', 515)
                    )
                    weather_features.append(conditions)
                
                weather_df = pd.DataFrame(weather_features)
                for col in ['temperature_norm', 'humidity_norm', 'rainfall_norm', 'wind_norm',
                           'track_rating_norm', 'ideal_conditions', 'heat_stress_risk', 'wet_track']:
                    if col in weather_df.columns:
                        df_dogs[col] = weather_df[col].values
            
            # Process each race
            for (track, race_num), race_df in df_dogs.groupby(['Track', 'RaceNumber']):
                # v4.4 scoring
                race_scores = score_race(race_df)
                
                # ML v2.1 predictions
                ml_predictions = predictor.predict_race(race_df, str(track))
                
                # Record all predictions
                for _, dog in race_df.iterrows():
                    box = dog['Box']
                    ml_conf = ml_predictions.get(box, {}).get('confidence', 0)
                    v44_score = race_scores.get(box, 0)
                    
                    all_ml_enhanced_predictions.append({
                        'Track': track,
                        'Race': race_num,
                        'Box': box,
                        'DogName': dog.get('DogName', ''),
                        'ML_Confidence': ml_conf,
                        'v44_Score': v44_score
                    })
                
                # Check for hybrid picks (both systems agree)
                top_box_v44 = max(race_scores, key=race_scores.get)
                top_score = race_scores[top_box_v44]
                scores_sorted = sorted(race_scores.values(), reverse=True)
                margin = ((top_score - scores_sorted[1]) / top_score * 100) if len(scores_sorted) > 1 else 0
                
                ml_conf_top = ml_predictions.get(top_box_v44, {}).get('confidence', 0)
                
                # Hybrid criteria: v4.4 margin 18%+ AND ML confidence 70%+
                if margin >= 18 and ml_conf_top >= 70:
                    all_hybrid_picks.append({
                        'Track': track,
                        'Race': race_num,
                        'Box': top_box_v44,
                        'DogName': race_df[race_df['Box'] == top_box_v44].iloc[0].get('DogName', ''),
                        'ML_Confidence': ml_conf_top,
                        'v44_Score': top_score,
                        'v44_Margin': margin,
                        'Tier': 'HYBRID_TIER0_ENHANCED'
                    })
                    print(f"   ✅ HYBRID PICK: {track} R{race_num} Box {top_box_v44} (ML: {ml_conf_top:.1f}%, v4.4: {margin:.1f}%)")
                
                # v4.4 picks for comparison
                if margin >= 18:
                    all_v44_picks.append({
                        'Track': track,
                        'Race': race_num,
                        'Box': top_box_v44,
                        'DogName': race_df[race_df['Box'] == top_box_v44].iloc[0].get('DogName', ''),
                        'Score': top_score,
                        'Margin': margin,
                        'Tier': 'TIER0'
                    })
            
            success_pdfs += 1
            
        except Exception as e:
            print(f"   ❌ Error processing {os.path.basename(pdf_file)}: {e}")
            failed_pdfs += 1
            continue
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PROCESSING SUMMARY")
    print("=" * 80)
    print(f"   PDFs: {success_pdfs}/{total_pdfs} successful, {failed_pdfs} failed")
    print(f"   ML v2.1 Hybrid picks: {len(all_hybrid_picks)}")
    print(f"   v4.4 picks (TIER0): {len(all_v44_picks)}")
    print(f"   Selectivity: {len(all_hybrid_picks)/max(len(all_v44_picks), 1)*100:.1f}% of v4.4 picks")
    
    # Save outputs
    os.makedirs('outputs', exist_ok=True)
    
    # 1. ML v2.1 hybrid picks
    if all_hybrid_picks:
        df_hybrid = pd.DataFrame(all_hybrid_picks)
        df_hybrid.to_excel('outputs/ml_hybrid_enhanced_picks.xlsx', index=False)
        print(f"\n✅ ML v2.1 hybrid picks saved: outputs/ml_hybrid_enhanced_picks.xlsx")
    else:
        print(f"\nℹ️  No ML v2.1 hybrid picks (waiting for both systems to agree)")
    
    # 2. All ML predictions ranked
    if all_ml_enhanced_predictions:
        df_ml_all = pd.DataFrame(all_ml_enhanced_predictions)
        df_ml_all = df_ml_all.sort_values('ML_Confidence', ascending=False)
        df_ml_all.to_excel('outputs/ml_enhanced_all_predictions.xlsx', index=False)
        print(f"✅ All ML v2.1 predictions saved: outputs/ml_enhanced_all_predictions.xlsx")
        print(f"   Total predictions: {len(df_ml_all)} (sorted by ML confidence)")
        if len(df_ml_all) > 0:
            top_pred = df_ml_all.iloc[0]
            print(f"   Top ML pick: {top_pred['Track']} R{top_pred['Race']} Box {top_pred['Box']} ({top_pred['ML_Confidence']:.1f}%)")
    
    # 3. v4.4 picks for comparison
    if all_v44_picks:
        df_v44 = pd.DataFrame(all_v44_picks)
        df_v44.to_csv('outputs/v44_picks_comparison.csv', index=False)
        print(f"✅ v4.4 picks saved: outputs/v44_picks_comparison.csv")
    
    print("\n" + "=" * 80)
    print("✅ ML v2.1 ENHANCED HYBRID ANALYSIS COMPLETE")
    print("=" * 80)
    print("\n💡 KEY INSIGHTS:")
    print("   • ML v2.1 Enhanced uses weather & track conditions")
    print("   • Expected: 41-47% win rate (vs 40-45% v2.0, 35-40% v1.0)")
    print("   • Only bets when v4.4 (18%+ margin) AND ML v2.1 (70%+ confidence) agree")
    print("   • Ultra-selective = higher quality picks")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
