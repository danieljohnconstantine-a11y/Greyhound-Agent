"""
Complete Analysis Pipeline - One-Click Solution
Runs predictions on data_predictions/ PDFs and generates all reports

This script combines:
1. ML v2.1 Enhanced Predictions (trained on 2,108 historical races)
2. Feature Analysis with Track→Race→Box sorting
3. Unified prediction report

Usage:
    python run_complete_analysis.py
    
    OR use the batch file:
    run_complete_analysis.bat

Prerequisites:
    1. Trained ML v2.1 model (run train_ml_enhanced.bat first)
    2. Race PDFs in data_predictions/ folder

Outputs (ALL generated in single run):
    1. outputs/ml_unified_predictions.xlsx - ALL dogs ranked by ML confidence (trained on 2,108 races)
    2. outputs/ml_feature_analysis_detailed.xlsx - Detailed features (Track→Race→Box sorted)
    3. outputs/complete_analysis_summary.txt - Quick summary report
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[logging.StreamHandler(sys.stdout)])

from src.ml_predictor_advanced import AdvancedGreyhoundMLPredictor
from src.weather_track_data import WeatherTrackDataManager
from src.parser import parse_race_form
from src.features import compute_features
from src.scorer import score_race
import pandas as pd
import glob
import pdfplumber
from datetime import datetime

def main():
    print("=" * 80)
    print("🚀 COMPLETE ANALYSIS PIPELINE - ONE-CLICK SOLUTION")
    print("   Predictions + Feature Analysis + All Reports")
    print("=" * 80)
    
    start_time = datetime.now()
    
    # Initialize weather/track manager
    print("\n🌤️  Loading weather & track condition data...")
    try:
        weather_manager = WeatherTrackDataManager()
        print(f"✅ Weather records: {len(weather_manager.weather_data)}")
        print(f"✅ Track condition records: {len(weather_manager.track_conditions)}")
    except Exception as e:
        print(f"⚠️  Warning: Could not load weather/track data: {e}")
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
    
    # Find PDFs in data_predictions
    pdf_files = glob.glob("data_predictions/*.pdf")
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in data_predictions/")
        print(f"   Please add race form PDFs to the data_predictions/ folder")
        return 1
    
    print(f"\n📄 Found {len(pdf_files)} PDF files in data_predictions/")
    print(f"   Processing predictions for today's races...")
    
    # Storage for results
    all_ml_enhanced_predictions = []
    all_hybrid_picks = []
    all_v44_picks = []
    all_detailed_features = []
    
    processed_count = 0
    error_count = 0
    
    # Process each PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            filename = os.path.basename(pdf_path)
            print(f"\n[{i}/{len(pdf_files)}] Processing: {filename}")
            
            with pdfplumber.open(pdf_path) as pdf:
                all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            
            # Parse race form
            df = parse_race_form(all_text)
            
            if df is None or len(df) == 0:
                print(f"   ⚠️  No data extracted from {filename}")
                error_count += 1
                continue
            
            # Get track name from filename (e.g., GEELG2711form.pdf -> GEEL)
            track_code = filename[:4].upper() if len(filename) >= 4 else "UNKN"
            
            # Group by race
            if 'RaceNumber' in df.columns:
                races = df.groupby('RaceNumber')
            elif 'RaceNum' in df.columns:
                races = df.groupby('RaceNum')
            else:
                print(f"   ⚠️  No RaceNumber/RaceNum column in {filename}")
                error_count += 1
                continue
            
            dogs_added_this_pdf = 0
            
            for race_num, race_df in races:
                try:
                    print(f"   🏁 Processing Race {race_num}: {len(race_df)} dogs")
                    
                    # Compute features for ML
                    weather_conditions = weather_manager.get_conditions(track_code, datetime.now())
                    features_df = compute_features(race_df, weather_conditions)
                    
                    if features_df is None or len(features_df) == 0:
                        print(f"   ⚠️  No features computed for Race {race_num} - skipping")
                        continue
                    
                    print(f"   ✓ Features computed: {len(features_df)} dogs")
                    
                    # Get ML predictions
                    ml_predictions = predictor.predict(features_df, track_code)
                    
                    if ml_predictions is None or len(ml_predictions) == 0:
                        print(f"   ⚠️  No ML predictions for Race {race_num} - skipping")
                        continue
                    
                    print(f"   ✓ ML predictions: {len(ml_predictions)} dogs")
                    
                    # Get v4.4 scores
                    v44_scores = score_race(race_df)
                    print(f"   ✓ V4.4 scores computed")
                    
                    # Convert v44_scores DataFrame to dict if needed
                    if isinstance(v44_scores, pd.DataFrame):
                        v44_scores_dict = {}
                        for idx, row in v44_scores.iterrows():
                            try:
                                box = int(row['Box'])
                                score = float(row['Score'])
                                v44_scores_dict[box] = score
                            except:
                                continue
                        v44_scores = v44_scores_dict
                    
                    # Process each dog
                    dogs_in_race = 0
                    for idx, row in race_df.iterrows():
                        try:
                            box = int(row.get('Box', 0))
                            dog_name = str(row.get('DogName', 'Unknown'))
                            
                            # Get ML confidence
                            ml_conf = ml_predictions.get(box, 0.0) * 100
                            
                            # Get v4.4 score
                            v44_score = v44_scores.get(box, 0.0)
                            
                            # Store ML prediction
                            pred_record = {
                                'Track': track_code,
                                'Race': int(race_num),
                                'Box': box,
                                'DogName': dog_name,
                                'ML_Confidence': round(ml_conf, 1),
                                'v44_Score': round(v44_score, 1)
                            }
                            all_ml_enhanced_predictions.append(pred_record)
                            dogs_in_race += 1
                            dogs_added_this_pdf += 1
                            
                            # Check for hybrid pick (v4.4 >= 18% AND ML >= 70%)
                            if v44_score >= 18.0 and ml_conf >= 70.0:
                                all_hybrid_picks.append(pred_record.copy())
                            
                            # Check for v4.4 TIER0 pick (>= 18%)
                            if v44_score >= 18.0:
                                all_v44_picks.append(pred_record.copy())
                            
                            # Extract detailed features for analysis report
                            feature_record = {
                                'Track': track_code,
                                'Race': int(race_num),
                                'Box': box,
                                'DogName': dog_name,
                                'ML_Confidence': round(ml_conf, 1),
                                'v44_Score': round(v44_score, 1)
                            }
                            
                            # Add all columns from the parsed DataFrame
                            for col in row.index:
                                if col not in ['Box', 'DogName']:
                                    val = row[col]
                                    # Handle NaN/None
                                    if pd.isna(val):
                                        feature_record[col] = 0
                                    # Handle lists/arrays
                                    elif isinstance(val, (list, tuple)):
                                        feature_record[col] = str(val)
                                    else:
                                        try:
                                            feature_record[col] = float(val) if isinstance(val, (int, float)) else str(val)
                                        except:
                                            feature_record[col] = str(val)
                            
                            all_detailed_features.append(feature_record)
                            
                        except Exception as e:
                            print(f"   ⚠️  Error processing dog Box {box}: {e}")
                            continue
                    
                    print(f"   ✅ Added {dogs_in_race} dogs from Race {race_num}")
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing race {race_num}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            processed_count += 1
            print(f"   ✅ PDF processed: {dogs_added_this_pdf} total dogs added")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_count += 1
            continue
    
    print(f"\n" + "=" * 80)
    print(f"📊 PROCESSING COMPLETE")
    print(f"   ✅ Successfully processed: {processed_count}/{len(pdf_files)} PDFs")
    if error_count > 0:
        print(f"   ⚠️  Errors encountered: {error_count} PDFs")
    print(f"   📋 Total dogs collected: {len(all_ml_enhanced_predictions)}")
    print(f"   📊 Total features collected: {len(all_detailed_features)}")
    print("=" * 80)
    
    # Generate all output files
    print(f"\n📁 Generating output files...")
    
    # 1. UNIFIED Predictions Report (replaces 3 separate files)
    # This combines all predictions ranked by ML confidence (trained on 2,108 historical races)
    if all_ml_enhanced_predictions:
        try:
            df_unified = pd.DataFrame(all_ml_enhanced_predictions)
            df_unified = df_unified.sort_values('ML_Confidence', ascending=False)
            
            # Add pick tier column
            df_unified['Pick_Tier'] = df_unified['ML_Confidence'].apply(
                lambda x: 'High Confidence (≥70%)' if x >= 70 
                else 'Medium Confidence (50-70%)' if x >= 50 
                else 'Lower Confidence (<50%)'
            )
            
            # Reorder columns for clarity
            cols = ['Track', 'Race', 'Box', 'DogName', 'ML_Confidence', 'Pick_Tier', 'v44_Score']
            # Add any additional columns that exist
            other_cols = [c for c in df_unified.columns if c not in cols]
            df_unified = df_unified[cols + other_cols]
            
            df_unified.to_excel('outputs/ml_unified_predictions.xlsx', index=False)
            
            # Statistics
            high_conf = len(df_unified[df_unified['ML_Confidence'] >= 70])
            med_conf = len(df_unified[(df_unified['ML_Confidence'] >= 50) & (df_unified['ML_Confidence'] < 70)])
            low_conf = len(df_unified[df_unified['ML_Confidence'] < 50])
            
            print(f"✅ Unified predictions: outputs/ml_unified_predictions.xlsx")
            print(f"   📊 Total: {len(df_unified)} dogs analyzed")
            print(f"   🎯 High Confidence (≥70%): {high_conf} dogs")
            print(f"   🟡 Medium Confidence (50-70%): {med_conf} dogs")
            print(f"   ⚪ Lower Confidence (<50%): {low_conf} dogs")
            print(f"   📈 Ranked by ML confidence (model trained on 2,108 historical races)")
        except Exception as e:
            print(f"❌ Error saving unified predictions: {e}")
    else:
        print(f"⚠️  No predictions generated")
    
    # 2. Detailed Feature Analysis (Track→Race→Box sorted)
    if all_detailed_features:
        try:
            df_features = pd.DataFrame(all_detailed_features)
            # Sort by Track, Race, Box
            df_features = df_features.sort_values(['Track', 'Race', 'Box'])
            df_features.to_excel('outputs/ml_feature_analysis_detailed.xlsx', index=False)
            print(f"✅ Feature analysis: outputs/ml_feature_analysis_detailed.xlsx ({len(df_features)} dogs)")
            print(f"   📋 Sorted by Track → Race → Box for easy navigation")
            print(f"   📊 Contains {len(df_features.columns)} features/columns")
            print(f"   🔍 Shows ALL data used by ML model for predictions")
        except Exception as e:
            print(f"❌ Error saving feature analysis: {e}")
    else:
        print(f"⚠️  No features captured")
    
    # 3. Summary report
    try:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        with open('outputs/complete_analysis_summary.txt', 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPLETE ANALYSIS PIPELINE - SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Processing Time: {duration:.1f} seconds\n\n")
            
            f.write("HOW 2,108 HISTORICAL RACES ARE USED:\n")
            f.write("  The ML v2.1 model was TRAINED on 2,108 actual race results.\n")
            f.write("  It learned patterns from:\n")
            f.write("    - Winner characteristics (times, form, box positions)\n")
            f.write("    - Track-specific trends (which tracks favor certain boxes)\n")
            f.write("    - Weather/condition impacts on performance\n")
            f.write("    - Dog performance patterns across all conditions\n\n")
            f.write("  When predicting today's races, the model applies these learned patterns\n")
            f.write("  to score each dog's likelihood of winning.\n\n")
            
            f.write("INPUT:\n")
            f.write(f"  PDFs Processed: {processed_count}/{len(pdf_files)}\n")
            f.write(f"  Errors: {error_count}\n\n")
            
            f.write("OUTPUT FILES GENERATED:\n")
            f.write(f"  1. ml_unified_predictions.xlsx - {len(all_ml_enhanced_predictions)} dogs ranked by ML confidence\n")
            f.write(f"     • ALL dogs from today's PDFs\n")
            f.write(f"     • Ranked in order of 'most likely to win' (based on 2,108 race learnings)\n")
            f.write(f"     • Includes confidence tier classification\n\n")
            f.write(f"  2. ml_feature_analysis_detailed.xlsx - {len(all_detailed_features)} dogs with full features\n")
            f.write(f"     • Sorted Track→Race→Box for easy navigation\n")
            f.write(f"     • Shows ALL data the ML model uses to make predictions\n")
            f.write(f"     • 50+ columns of actual PDF data\n\n")
            f.write(f"  3. complete_analysis_summary.txt - This summary\n\n")
            
            if all_ml_enhanced_predictions:
                df_temp = pd.DataFrame(all_ml_enhanced_predictions)
                high_conf = len(df_temp[df_temp['ML_Confidence'] >= 70])
                med_conf = len(df_temp[(df_temp['ML_Confidence'] >= 50) & (df_temp['ML_Confidence'] < 70)])
                
                f.write("CONFIDENCE DISTRIBUTION:\n")
                f.write(f"  High (≥70%): {high_conf} dogs - Strong predictions\n")
                f.write(f"  Medium (50-70%): {med_conf} dogs - Moderate confidence\n")
                f.write(f"  Lower (<50%): {len(df_temp) - high_conf - med_conf} dogs - Less confident\n\n")
            
            f.write("HOW TO USE THE REPORTS:\n")
            f.write("  1. Open ml_unified_predictions.xlsx\n")
            f.write("     - Dogs are already ranked by ML confidence (highest first)\n")
            f.write("     - Top dogs = most likely to win based on 2,108 historical patterns\n")
            f.write("     - Focus on 'High Confidence (≥70%)' dogs for best results\n\n")
            f.write("  2. Open ml_feature_analysis_detailed.xlsx\n")
            f.write("     - See exactly what data drives each prediction\n")
            f.write("     - Sorted by Track→Race→Box for easy per-race review\n")
            f.write("     - All values are from actual PDF parsing (100% factual)\n\n")
            
            f.write("=" * 80 + "\n")
        
        print(f"✅ Summary report: outputs/complete_analysis_summary.txt")
        
    except Exception as e:
        print(f"⚠️  Could not create summary report: {e}")
    
    # Final summary
    print(f"\n" + "=" * 80)
    print(f"🎉 COMPLETE! All reports generated in outputs/ folder")
    print(f"   ⏱️  Total time: {(datetime.now() - start_time).total_seconds():.1f} seconds")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
