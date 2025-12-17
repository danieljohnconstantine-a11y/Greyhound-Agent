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
    - outputs/ml_enhanced_all_predictions.xlsx - ALL dogs with ML scores (DIAGNOSTIC)
    - outputs/ml_hybrid_enhanced_picks.xlsx - High-confidence hybrid picks only
    - outputs/v44_picks_comparison.csv - v4.4 picks for comparison
    - outputs/ml_feature_analysis_detailed.xlsx - DETAILED feature breakdown (NEW!)
    
Note: ml_enhanced_all_predictions.xlsx is ALWAYS created (even if empty) to verify
      the pipeline is working. It shows every dog analyzed with their ML confidence
      score, sorted from highest to lowest.
      
      ml_feature_analysis_detailed.xlsx shows ALL features used to determine scores,
      including basic info (track, race, dog name), form data (times, win rates),
      computed ML features (speed rating, consistency), and weather/track conditions.
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
    all_detailed_features = []  # NEW: Store all features for detailed analysis
    
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
                race_scored_df = score_race(race_df)
                
                # Convert DataFrame to dict: Box -> FinalScore
                # Ensure Box is integer and FinalScore is numeric
                race_scores = {}
                for idx, row in race_scored_df.iterrows():
                    try:
                        box_int = int(row['Box'])
                        score_float = float(row.get('FinalScore', 0))
                        race_scores[box_int] = score_float
                    except (ValueError, TypeError):
                        # Skip invalid box/score values
                        continue
                
                # ML v2.1 predictions
                ml_confidences = predictor.predict_confidence(race_df)
                
                # Create box to confidence mapping
                ml_predictions = {}
                for idx, row in race_df.iterrows():
                    try:
                        box_int = int(row['Box'])
                        ml_predictions[box_int] = ml_confidences.loc[idx] if idx in ml_confidences.index else 0
                    except (ValueError, TypeError):
                        continue
                
                # Record all predictions AND detailed features
                for idx, dog in race_df.iterrows():
                    try:
                        box_int = int(dog['Box'])
                        ml_conf = ml_predictions.get(box_int, 0)
                        v44_score = race_scores.get(box_int, 0)
                        
                        all_ml_enhanced_predictions.append({
                            'Track': track,
                            'Race': race_num,
                            'Box': box_int,
                            'DogName': dog.get('DogName', ''),
                            'ML_Confidence': ml_conf,
                            'v44_Score': v44_score
                        })
                        
                        # NEW: Capture detailed features for feature analysis report
                        feature_record = {
                            'Track': track,
                            'Race': race_num,
                            'Box': box_int,
                            'DogName': dog.get('DogName', ''),
                            'ML_Confidence': ml_conf,
                            'v44_Score': v44_score,
                            
                            # Basic info
                            'Date': dog.get('Date', ''),
                            'Distance': dog.get('Distance', 0),
                            'StartType': dog.get('StartType', ''),
                            'Grade': dog.get('Grade', ''),
                            'Weight': dog.get('Weight', 0),
                            
                            # Form features
                            'BestTime': dog.get('BestTime', 0),
                            'LastTime': dog.get('LastTime', 0),
                            'AvgTime': dog.get('AvgTime', 0),
                            'TimeConsistency': dog.get('TimeConsistency', 0),
                            'RecentForm': dog.get('RecentForm', ''),
                            'WinRate': dog.get('WinRate', 0),
                            'PlaceRate': dog.get('PlaceRate', 0),
                            'Starts': dog.get('Starts', 0),
                            'Wins': dog.get('Wins', 0),
                            'Seconds': dog.get('Seconds', 0),
                            'Thirds': dog.get('Thirds', 0),
                            
                            # Computed features (ML features)
                            'speed_rating': dog.get('speed_rating', 0),
                            'consistency_score': dog.get('consistency_score', 0),
                            'recent_performance': dog.get('recent_performance', 0),
                            'box_advantage': dog.get('box_advantage', 0),
                            'win_momentum': dog.get('win_momentum', 0),
                            'place_momentum': dog.get('place_momentum', 0),
                            'time_improvement': dog.get('time_improvement', 0),
                            'fitness_trend': dog.get('fitness_trend', 0),
                            
                            # Weather/Track features (if available)
                            'temperature_norm': dog.get('temperature_norm', 0),
                            'humidity_norm': dog.get('humidity_norm', 0),
                            'rainfall_norm': dog.get('rainfall_norm', 0),
                            'wind_norm': dog.get('wind_norm', 0),
                            'track_rating_norm': dog.get('track_rating_norm', 0),
                            'ideal_conditions': dog.get('ideal_conditions', 0),
                            'heat_stress_risk': dog.get('heat_stress_risk', 0),
                            'wet_track': dog.get('wet_track', 0),
                        }
                        all_detailed_features.append(feature_record)
                        
                    except (ValueError, TypeError):
                        # Skip dogs with invalid box numbers
                        continue
                
                # Check for hybrid picks (both systems agree)
                if not race_scores:
                    # Skip if no valid scores
                    continue
                    
                top_box_v44 = max(race_scores, key=race_scores.get)
                top_score = race_scores[top_box_v44]
                scores_sorted = sorted(race_scores.values(), reverse=True)
                margin = ((top_score - scores_sorted[1]) / top_score * 100) if len(scores_sorted) > 1 else 0
                
                ml_conf_top = ml_predictions.get(top_box_v44, 0)
                
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
            import traceback
            print(f"   ❌ Error processing {os.path.basename(pdf_file)}: {e}")
            print(f"   📋 Full traceback:")
            traceback.print_exc()
            failed_pdfs += 1
            continue
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PROCESSING SUMMARY")
    print("=" * 80)
    print(f"   PDFs: {success_pdfs}/{total_pdfs} successful, {failed_pdfs} failed")
    print(f"   ML v2.1 Hybrid picks: {len(all_hybrid_picks)}")
    print(f"   v4.4 picks (TIER0): {len(all_v44_picks)}")
    print(f"   Total ML predictions: {len(all_ml_enhanced_predictions)}")
    print(f"   Selectivity: {len(all_hybrid_picks)/max(len(all_v44_picks), 1)*100:.1f}% of v4.4 picks")
    
    # Check if any PDFs were successfully processed
    if success_pdfs == 0:
        print("\n❌ ERROR: No PDFs were successfully processed!")
        print("   Check the error messages above for details.")
        print("   Common issues:")
        print("   • PDF format not recognized")
        print("   • Missing required data in PDFs")
        print("   • Model compatibility issues")
        return 1
    
    # Save outputs
    os.makedirs('outputs', exist_ok=True)
    
    # 1. ML v2.1 hybrid picks
    if all_hybrid_picks:
        try:
            df_hybrid = pd.DataFrame(all_hybrid_picks)
            df_hybrid.to_excel('outputs/ml_hybrid_enhanced_picks.xlsx', index=False)
            print(f"\n✅ ML v2.1 hybrid picks saved: outputs/ml_hybrid_enhanced_picks.xlsx")
        except Exception as e:
            print(f"\n❌ Error saving hybrid picks to Excel: {e}")
            print(f"   Attempting to save as CSV instead...")
            try:
                df_hybrid.to_csv('outputs/ml_hybrid_enhanced_picks.csv', index=False)
                print(f"✅ Saved as CSV: outputs/ml_hybrid_enhanced_picks.csv")
            except Exception as e2:
                print(f"❌ Failed to save even as CSV: {e2}")
    else:
        print(f"\nℹ️  No ML v2.1 hybrid picks (criteria: v4.4 margin ≥18% AND ML confidence ≥70%)")
        if all_v44_picks:
            print(f"   • v4.4 found {len(all_v44_picks)} picks, but ML confidence was too low")
        elif all_ml_enhanced_predictions:
            print(f"   • ML made {len(all_ml_enhanced_predictions)} predictions, but v4.4 margins were too low")
    
    # 2. All ML predictions ranked (ALWAYS create this file - diagnostic purposes)
    if all_ml_enhanced_predictions:
        try:
            df_ml_all = pd.DataFrame(all_ml_enhanced_predictions)
            df_ml_all = df_ml_all.sort_values('ML_Confidence', ascending=False)
            df_ml_all.to_excel('outputs/ml_enhanced_all_predictions.xlsx', index=False)
            print(f"\n✅ ALL DOGS WITH ML SCORES saved: outputs/ml_enhanced_all_predictions.xlsx")
            print(f"   📊 Total dogs analyzed: {len(df_ml_all)} (sorted highest to lowest ML confidence)")
            if len(df_ml_all) > 0:
                top_pred = df_ml_all.iloc[0]
                print(f"   🏆 Highest ML score: {top_pred['Track']} R{top_pred['Race']} Box {top_pred['Box']} - {top_pred['DogName']}")
                print(f"      ML Confidence: {top_pred['ML_Confidence']:.1f}%, v4.4 Score: {top_pred['v44_Score']:.1f}")
                
                # Show summary statistics
                high_conf = len(df_ml_all[df_ml_all['ML_Confidence'] >= 70])
                med_conf = len(df_ml_all[(df_ml_all['ML_Confidence'] >= 50) & (df_ml_all['ML_Confidence'] < 70)])
                print(f"\n   📈 Confidence Distribution:")
                print(f"      High (≥70%): {high_conf} dogs")
                print(f"      Medium (50-70%): {med_conf} dogs")
                print(f"      Lower (<50%): {len(df_ml_all) - high_conf - med_conf} dogs")
        except Exception as e:
            print(f"\n❌ Error saving ML predictions to Excel: {e}")
            print(f"   Attempting to save as CSV instead...")
            try:
                df_ml_all.to_csv('outputs/ml_enhanced_all_predictions.csv', index=False)
                print(f"✅ Saved as CSV: outputs/ml_enhanced_all_predictions.csv")
            except Exception as e2:
                print(f"❌ Failed to save even as CSV: {e2}")
    else:
        # Create empty file to show pipeline ran but no predictions
        print(f"\n⚠️  No ML predictions generated (all PDFs may have failed to process)")
        print(f"   Creating empty diagnostic file...")
        try:
            df_empty = pd.DataFrame(columns=['Track', 'Race', 'Box', 'DogName', 'ML_Confidence', 'v44_Score'])
            df_empty.to_excel('outputs/ml_enhanced_all_predictions.xlsx', index=False)
            print(f"✅ Empty diagnostic file created: outputs/ml_enhanced_all_predictions.xlsx")
            print(f"   (File exists but contains no predictions - indicates processing issues)")
        except Exception as e:
            print(f"❌ Failed to create diagnostic file: {e}")
    
    # 3. v4.4 picks for comparison
    if all_v44_picks:
        try:
            df_v44 = pd.DataFrame(all_v44_picks)
            df_v44.to_csv('outputs/v44_picks_comparison.csv', index=False)
            print(f"✅ v4.4 picks saved: outputs/v44_picks_comparison.csv")
        except Exception as e:
            print(f"❌ Error saving v4.4 picks: {e}")
    else:
        print(f"ℹ️  No v4.4 TIER0 picks (no races met 18%+ margin criterion)")
    
    # 4. NEW: Detailed Feature Analysis Report (ALWAYS created)
    if all_detailed_features:
        try:
            df_features = pd.DataFrame(all_detailed_features)
            # Sort by ML confidence for easy review
            df_features = df_features.sort_values('ML_Confidence', ascending=False)
            df_features.to_excel('outputs/ml_feature_analysis_detailed.xlsx', index=False)
            print(f"\n✅ DETAILED FEATURE ANALYSIS saved: outputs/ml_feature_analysis_detailed.xlsx")
            print(f"   📋 Complete dataset with ALL features used for scoring")
            print(f"   📊 Total records: {len(df_features)} dogs")
            print(f"   📈 Includes: Basic info, form data, ML features, weather/track conditions")
            print(f"   💡 Use this to understand what data drives the ML confidence scores")
        except Exception as e:
            print(f"\n❌ Error saving detailed feature analysis to Excel: {e}")
            print(f"   Attempting to save as CSV instead...")
            try:
                df_features.to_csv('outputs/ml_feature_analysis_detailed.csv', index=False)
                print(f"✅ Saved as CSV: outputs/ml_feature_analysis_detailed.csv")
            except Exception as e2:
                print(f"❌ Failed to save even as CSV: {e2}")
    else:
        print(f"\n⚠️  No detailed features captured (all PDFs may have failed)")
        try:
            # Create empty template to show expected columns
            df_empty_features = pd.DataFrame(columns=[
                'Track', 'Race', 'Box', 'DogName', 'ML_Confidence', 'v44_Score',
                'Date', 'Distance', 'StartType', 'Grade', 'Weight',
                'BestTime', 'LastTime', 'AvgTime', 'TimeConsistency', 'RecentForm',
                'WinRate', 'PlaceRate', 'Starts', 'Wins', 'Seconds', 'Thirds',
                'speed_rating', 'consistency_score', 'recent_performance', 'box_advantage',
                'win_momentum', 'place_momentum', 'time_improvement', 'fitness_trend',
                'temperature_norm', 'humidity_norm', 'rainfall_norm', 'wind_norm',
                'track_rating_norm', 'ideal_conditions', 'heat_stress_risk', 'wet_track'
            ])
            df_empty_features.to_excel('outputs/ml_feature_analysis_detailed.xlsx', index=False)
            print(f"✅ Empty template created: outputs/ml_feature_analysis_detailed.xlsx")
        except Exception as e:
            print(f"❌ Failed to create template: {e}")
    
    print("\n" + "=" * 80)
    print("✅ ML v2.1 ENHANCED HYBRID ANALYSIS COMPLETE")
    print("=" * 80)
    print("\n💡 KEY INSIGHTS:")
    print("   • ML v2.1 Enhanced uses weather & track conditions")
    print("   • Expected: 41-47% win rate (vs 40-45% v2.0, 35-40% v1.0)")
    print("   • Only bets when v4.4 (18%+ margin) AND ML v2.1 (70%+ confidence) agree")
    print("   • Ultra-selective = higher quality picks")
    print("\n📁 OUTPUT FILES:")
    print("   1. ml_enhanced_all_predictions.xlsx - ALL dogs with ML scores (diagnostic)")
    print("   2. ml_hybrid_enhanced_picks.xlsx - High-confidence hybrid picks only")
    print("   3. v44_picks_comparison.csv - v4.4 picks for comparison")
    print("   4. ml_feature_analysis_detailed.xlsx - Complete feature breakdown (NEW!)")
    print("\n💡 TIPS:")
    print("   • Check ml_enhanced_all_predictions.xlsx to verify pipeline is working")
    print("   • Use ml_feature_analysis_detailed.xlsx to understand what drives ML scores")
    print("   • Features include: form data, speed ratings, weather/track conditions, and more")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
