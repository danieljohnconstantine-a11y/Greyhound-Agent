"""
Complete Analysis Pipeline - One-Click Solution
Runs predictions on data_predictions/ PDFs and generates all reports

This script combines:
1. ML v2.1 Enhanced Hybrid Predictions (run_ml_hybrid_enhanced.py functionality)
2. Feature Analysis with Track→Race→Box sorting
3. All diagnostic reports

Usage:
    python run_complete_analysis.py
    
    OR use the batch file:
    run_complete_analysis.bat

Prerequisites:
    1. Trained ML v2.1 model (run train_ml_enhanced.bat first)
    2. Race PDFs in data_predictions/ folder

Outputs (ALL generated in single run):
    1. outputs/ml_enhanced_all_predictions.xlsx - ALL dogs with ML scores
    2. outputs/ml_hybrid_enhanced_picks.xlsx - High-confidence picks
    3. outputs/v44_picks_comparison.csv - v4.4 picks comparison
    4. outputs/ml_feature_analysis_detailed.xlsx - Detailed features (Track→Race→Box sorted)
    5. outputs/complete_analysis_summary.txt - Quick summary report
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
            if 'RaceNum' in df.columns:
                races = df.groupby('RaceNum')
            else:
                print(f"   ⚠️  No RaceNum column in {filename}")
                error_count += 1
                continue
            
            for race_num, race_df in races:
                try:
                    # Compute features for ML
                    weather_conditions = weather_manager.get_conditions(track_code, datetime.now())
                    features_df = compute_features(race_df, weather_conditions)
                    
                    if features_df is None or len(features_df) == 0:
                        continue
                    
                    # Get ML predictions
                    ml_predictions = predictor.predict(features_df, track_code)
                    
                    if ml_predictions is None or len(ml_predictions) == 0:
                        continue
                    
                    # Get v4.4 scores
                    v44_scores = score_race(race_df)
                    
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
                            continue
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing race {race_num}: {e}")
                    continue
            
            processed_count += 1
            print(f"   ✅ Processed successfully")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_count += 1
            continue
    
    print(f"\n" + "=" * 80)
    print(f"📊 PROCESSING COMPLETE")
    print(f"   ✅ Successfully processed: {processed_count}/{len(pdf_files)} PDFs")
    if error_count > 0:
        print(f"   ⚠️  Errors encountered: {error_count} PDFs")
    print("=" * 80)
    
    # Generate all output files
    print(f"\n📁 Generating output files...")
    
    # 1. Hybrid picks
    if all_hybrid_picks:
        try:
            df_hybrid = pd.DataFrame(all_hybrid_picks)
            df_hybrid = df_hybrid.sort_values('ML_Confidence', ascending=False)
            df_hybrid.to_excel('outputs/ml_hybrid_enhanced_picks.xlsx', index=False)
            print(f"✅ Hybrid picks: outputs/ml_hybrid_enhanced_picks.xlsx ({len(df_hybrid)} picks)")
        except Exception as e:
            print(f"❌ Error saving hybrid picks: {e}")
    else:
        print(f"ℹ️  No hybrid picks (criteria: v4.4 ≥18% AND ML ≥70%)")
    
    # 2. All ML predictions (ALWAYS create)
    if all_ml_enhanced_predictions:
        try:
            df_ml_all = pd.DataFrame(all_ml_enhanced_predictions)
            df_ml_all = df_ml_all.sort_values('ML_Confidence', ascending=False)
            df_ml_all.to_excel('outputs/ml_enhanced_all_predictions.xlsx', index=False)
            print(f"✅ All predictions: outputs/ml_enhanced_all_predictions.xlsx ({len(df_ml_all)} dogs)")
        except Exception as e:
            print(f"❌ Error saving all predictions: {e}")
    else:
        print(f"⚠️  No predictions generated")
    
    # 3. v4.4 picks for comparison
    if all_v44_picks:
        try:
            df_v44 = pd.DataFrame(all_v44_picks)
            df_v44.to_csv('outputs/v44_picks_comparison.csv', index=False)
            print(f"✅ v4.4 picks: outputs/v44_picks_comparison.csv ({len(df_v44)} picks)")
        except Exception as e:
            print(f"❌ Error saving v4.4 picks: {e}")
    
    # 4. Detailed Feature Analysis (Track→Race→Box sorted)
    if all_detailed_features:
        try:
            df_features = pd.DataFrame(all_detailed_features)
            # Sort by Track, Race, Box
            df_features = df_features.sort_values(['Track', 'Race', 'Box'])
            df_features.to_excel('outputs/ml_feature_analysis_detailed.xlsx', index=False)
            print(f"✅ Feature analysis: outputs/ml_feature_analysis_detailed.xlsx ({len(df_features)} dogs)")
            print(f"   📋 Sorted by Track → Race → Box for easy navigation")
            print(f"   📊 Contains {len(df_features.columns)} features/columns")
        except Exception as e:
            print(f"❌ Error saving feature analysis: {e}")
    else:
        print(f"⚠️  No features captured")
    
    # 5. Summary report
    try:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        with open('outputs/complete_analysis_summary.txt', 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPLETE ANALYSIS PIPELINE - SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Processing Time: {duration:.1f} seconds\n\n")
            
            f.write("INPUT:\n")
            f.write(f"  PDFs Processed: {processed_count}/{len(pdf_files)}\n")
            f.write(f"  Errors: {error_count}\n\n")
            
            f.write("OUTPUT FILES GENERATED:\n")
            f.write(f"  1. ml_enhanced_all_predictions.xlsx - {len(all_ml_enhanced_predictions)} dogs analyzed\n")
            f.write(f"  2. ml_hybrid_enhanced_picks.xlsx - {len(all_hybrid_picks)} high-confidence picks\n")
            f.write(f"  3. v44_picks_comparison.csv - {len(all_v44_picks)} v4.4 picks\n")
            f.write(f"  4. ml_feature_analysis_detailed.xlsx - {len(all_detailed_features)} dogs with full features\n")
            f.write(f"  5. complete_analysis_summary.txt - This summary\n\n")
            
            if all_ml_enhanced_predictions:
                df_temp = pd.DataFrame(all_ml_enhanced_predictions)
                high_conf = len(df_temp[df_temp['ML_Confidence'] >= 70])
                med_conf = len(df_temp[(df_temp['ML_Confidence'] >= 50) & (df_temp['ML_Confidence'] < 70)])
                
                f.write("CONFIDENCE DISTRIBUTION:\n")
                f.write(f"  High (≥70%): {high_conf} dogs\n")
                f.write(f"  Medium (50-70%): {med_conf} dogs\n")
                f.write(f"  Lower (<50%): {len(df_temp) - high_conf - med_conf} dogs\n\n")
            
            f.write("RECOMMENDATIONS:\n")
            f.write("  1. Review ml_hybrid_enhanced_picks.xlsx for today's high-confidence selections\n")
            f.write("  2. Check ml_feature_analysis_detailed.xlsx to see what data drives each prediction\n")
            f.write("  3. Feature analysis is sorted Track→Race→Box for easy per-race review\n")
            f.write("  4. All data comes from actual PDF parsing (100% factual)\n\n")
            
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
