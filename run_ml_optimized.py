"""
Optimized ML Prediction System - Targeting 50%+ Win Rate

This script uses optimized ML confidence thresholds based on backtest analysis
to achieve maximum win rate while maintaining reasonable bet volume.

Features:
- Configurable ML confidence threshold
- Minimum confidence spread filtering (avoid close races)
- Track-specific filtering (focus on high-performing tracks)
- Top N picks per race option
- Detailed confidence reporting

Usage:
    python run_ml_optimized.py [--threshold 60] [--min-spread 10] [--top-n 2]
    
    --threshold: Minimum ML confidence percentage (default: 60)
    --min-spread: Minimum lead over 2nd place in percentage points (default: 10)
    --top-n: Pick top N dogs per race (default: 1, 0 = use threshold only)
    --tracks: Comma-separated list of tracks to include (default: all)

Examples:
    # Use backtest-recommended settings
    python run_ml_optimized.py --threshold 60 --min-spread 10
    
    # Pick top 2 dogs per race at 55% confidence
    python run_ml_optimized.py --threshold 55 --top-n 2
    
    # Only specific tracks
    python run_ml_optimized.py --threshold 60 --tracks "Richmond,Wentworth Park,The Meadows"

Prerequisites:
    1. Trained ML v2.1 model (models/greyhound_ml_v2.1_enhanced.pkl)
    2. Race PDFs in data_predictions/ folder
    3. Run backtest_analyze.py first to find optimal thresholds

Outputs:
    - outputs/ml_optimized_picks.xlsx - Optimized picks for 50%+ win rate
    - outputs/ml_optimized_all_predictions.xlsx - All predictions with confidence
    - outputs/ml_optimized_report.txt - Detailed analysis report
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.ml_predictor_advanced import AdvancedGreyhoundMLPredictor
from src.weather_track_data import WeatherTrackDataManager
from src.parser import parse_race_form
from src.features import compute_features
import pandas as pd
import numpy as np
import glob
import pdfplumber
from datetime import datetime
import argparse

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Optimized ML Predictions for 50%+ Win Rate')
    parser.add_argument('--threshold', type=float, default=60.0,
                       help='Minimum ML confidence percentage (default: 60)')
    parser.add_argument('--min-spread', type=float, default=10.0,
                       help='Minimum confidence lead over 2nd place in percentage points (default: 10)')
    parser.add_argument('--top-n', type=int, default=1,
                       help='Pick top N dogs per race (default: 1, set 0 to use threshold only)')
    parser.add_argument('--tracks', type=str, default='',
                       help='Comma-separated list of tracks to include (default: all)')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    print("=" * 80)
    print("🎯 OPTIMIZED ML PREDICTION SYSTEM - Targeting 50%+ Win Rate")
    print("=" * 80)
    print(f"\n⚙️  Configuration:")
    print(f"   ML Confidence Threshold: {args.threshold}%")
    print(f"   Minimum Confidence Spread: {args.min_spread} percentage points")
    print(f"   Selection Mode: {'Top ' + str(args.top_n) + ' per race' if args.top_n > 0 else 'Threshold-based'}")
    if args.tracks:
        print(f"   Track Filter: {args.tracks}")
    else:
        print(f"   Track Filter: All tracks")
    
    # Parse track filter
    allowed_tracks = set()
    if args.tracks:
        allowed_tracks = set(t.strip() for t in args.tracks.split(','))
    
    # Load model
    print("\n📥 Loading ML v2.1 model...")
    model_path = "models/greyhound_ml_v2.1_enhanced.pkl"
    
    if not os.path.exists(model_path):
        print(f"❌ ERROR: Model not found at {model_path}")
        print("   Please run train_ml_enhanced.bat first")
        return 1
    
    try:
        predictor = AdvancedGreyhoundMLPredictor()
        predictor.load_model(model_path)
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return 1
    
    # Initialize weather manager
    print("\n🌤️  Loading weather & track condition data...")
    try:
        weather_manager = WeatherTrackDataManager()
        print("✅ Weather data loaded")
    except Exception as e:
        print(f"⚠️  Warning: {e}")
        weather_manager = WeatherTrackDataManager()
    
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
    all_predictions = []
    optimized_picks = []
    
    total_pdfs = len(pdf_files)
    success_pdfs = 0
    failed_pdfs = 0
    filtered_races = 0
    selected_races = 0
    
    for idx, pdf_file in enumerate(sorted(pdf_files), 1):
        print(f"\n🔍 Processing ({idx}/{total_pdfs}): {os.path.basename(pdf_file)}")
        
        try:
            # Extract and parse PDF
            with pdfplumber.open(pdf_file) as pdf:
                text = "".join(page.extract_text() + "\n" for page in pdf.pages)
            
            df_dogs = parse_race_form(text)
            if df_dogs is None or len(df_dogs) == 0:
                print(f"   ⚠️  No data parsed")
                failed_pdfs += 1
                continue
            
            print(f"   ✅ Parsed {len(df_dogs)} dogs")
            
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
                # Apply track filter if specified
                if allowed_tracks and track not in allowed_tracks:
                    filtered_races += 1
                    continue
                
                # Get ML predictions
                ml_confidences = predictor.predict_confidence(race_df)
                
                # Create box to confidence mapping
                ml_predictions = {}
                dog_names = {}
                for idx_row, row in race_df.iterrows():
                    try:
                        box_int = int(row['Box'])
                        ml_predictions[box_int] = ml_confidences.loc[idx_row] if idx_row in ml_confidences.index else 0
                        dog_names[box_int] = row.get('DogName', '')
                    except:
                        continue
                
                if not ml_predictions:
                    continue
                
                # Record all predictions
                for box, conf in ml_predictions.items():
                    all_predictions.append({
                        'Track': track,
                        'Race': race_num,
                        'Box': box,
                        'DogName': dog_names.get(box, ''),
                        'ML_Confidence': conf
                    })
                
                # Sort by confidence
                sorted_boxes = sorted(ml_predictions.items(), key=lambda x: x[1], reverse=True)
                
                # Apply selection logic
                if args.top_n > 0:
                    # Pick top N dogs
                    for i in range(min(args.top_n, len(sorted_boxes))):
                        box, conf = sorted_boxes[i]
                        if conf >= args.threshold:
                            # Check confidence spread for top pick
                            if i == 0 and len(sorted_boxes) > 1:
                                spread = sorted_boxes[0][1] - sorted_boxes[1][1]
                                if spread < args.min_spread:
                                    print(f"   ⚠️  {track} R{race_num}: Insufficient spread ({spread:.1f}%), skipping")
                                    continue
                            
                            optimized_picks.append({
                                'Track': track,
                                'Race': race_num,
                                'Box': box,
                                'DogName': dog_names.get(box, ''),
                                'ML_Confidence': conf,
                                'Rank': i + 1
                            })
                            
                            if i == 0:
                                print(f"   ✅ PICK: {track} R{race_num} Box {box} (ML: {conf:.1f}%)")
                                selected_races += 1
                            else:
                                print(f"      ↳ ALT: Box {box} (ML: {conf:.1f}%)")
                else:
                    # Threshold-based selection
                    top_box, top_conf = sorted_boxes[0]
                    
                    if top_conf >= args.threshold:
                        # Check confidence spread
                        if len(sorted_boxes) > 1:
                            spread = sorted_boxes[0][1] - sorted_boxes[1][1]
                            if spread < args.min_spread:
                                print(f"   ⚠️  {track} R{race_num}: Insufficient spread ({spread:.1f}%), skipping")
                                continue
                        
                        optimized_picks.append({
                            'Track': track,
                            'Race': race_num,
                            'Box': top_box,
                            'DogName': dog_names.get(top_box, ''),
                            'ML_Confidence': top_conf,
                            'Rank': 1
                        })
                        
                        print(f"   ✅ PICK: {track} R{race_num} Box {top_box} (ML: {top_conf:.1f}%)")
                        selected_races += 1
            
            success_pdfs += 1
            
        except Exception as e:
            import traceback
            print(f"   ❌ Error: {e}")
            print(f"   📋 Full traceback:")
            traceback.print_exc()
            failed_pdfs += 1
            continue
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PROCESSING SUMMARY")
    print("=" * 80)
    print(f"   PDFs: {success_pdfs}/{total_pdfs} successful, {failed_pdfs} failed")
    print(f"   Races analyzed: {len(all_predictions) // 8 if all_predictions else 0}")  # Approx 8 dogs per race
    print(f"   Races filtered (track): {filtered_races}")
    print(f"   Races selected: {selected_races}")
    print(f"   Optimized picks: {len(optimized_picks)}")
    print(f"   Total predictions recorded: {len(all_predictions)}")
    
    if len(optimized_picks) > 0:
        avg_conf = sum(p['ML_Confidence'] for p in optimized_picks) / len(optimized_picks)
        print(f"   Average ML confidence: {avg_conf:.1f}%")
    
    # Save results
    os.makedirs("outputs", exist_ok=True)
    
    if len(optimized_picks) > 0:
        # Optimized picks Excel
        df_picks = pd.DataFrame(optimized_picks)
        df_picks = df_picks.sort_values('ML_Confidence', ascending=False)
        picks_file = "outputs/ml_optimized_picks.xlsx"
        df_picks.to_excel(picks_file, index=False)
        print(f"\n✅ Optimized picks saved: {picks_file}")
        
        # Detailed report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("OPTIMIZED ML PREDICTIONS REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("CONFIGURATION:")
        report_lines.append(f"  ML Confidence Threshold: {args.threshold}%")
        report_lines.append(f"  Minimum Confidence Spread: {args.min_spread} percentage points")
        report_lines.append(f"  Selection Mode: {'Top ' + str(args.top_n) + ' per race' if args.top_n > 0 else 'Threshold-based'}")
        report_lines.append(f"  Track Filter: {args.tracks if args.tracks else 'All tracks'}")
        report_lines.append("")
        report_lines.append("RESULTS:")
        report_lines.append(f"  Total Picks: {len(optimized_picks)}")
        report_lines.append(f"  Average Confidence: {avg_conf:.1f}%")
        report_lines.append(f"  Selectivity: {selected_races}/{selected_races + filtered_races if selected_races + filtered_races > 0 else 'N/A'} races")
        report_lines.append("")
        report_lines.append("PICKS BY TRACK:")
        report_lines.append("-" * 80)
        
        track_summary = {}
        for pick in optimized_picks:
            track = pick['Track']
            if track not in track_summary:
                track_summary[track] = {'count': 0, 'avg_conf': []}
            track_summary[track]['count'] += 1
            track_summary[track]['avg_conf'].append(pick['ML_Confidence'])
        
        for track in sorted(track_summary.keys()):
            count = track_summary[track]['count']
            avg = sum(track_summary[track]['avg_conf']) / count
            report_lines.append(f"  {track}: {count} picks (Avg Confidence: {avg:.1f}%)")
        
        report_lines.append("")
        report_lines.append("DETAILED PICKS:")
        report_lines.append("-" * 80)
        report_lines.append(f"{'Track':<20} {'Race':<6} {'Box':<5} {'Dog Name':<25} {'ML Conf':<10}")
        report_lines.append("-" * 80)
        
        for pick in sorted(optimized_picks, key=lambda x: (x['Track'], x['Race'])):
            report_lines.append(f"{pick['Track']:<20} {pick['Race']:<6} {pick['Box']:<5} "
                              f"{pick['DogName']:<25} {pick['ML_Confidence']:.1f}%")
        
        report_file = "outputs/ml_optimized_report.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✅ Detailed report saved: {report_file}")
    else:
        print("\n⚠️  No picks met the criteria!")
        print("   Consider lowering the threshold or min-spread settings")
    
    # Save all predictions
    if len(all_predictions) > 0:
        df_all = pd.DataFrame(all_predictions)
        df_all = df_all.sort_values('ML_Confidence', ascending=False)
        all_file = "outputs/ml_optimized_all_predictions.xlsx"
        df_all.to_excel(all_file, index=False)
        print(f"✅ All predictions saved: {all_file}")
    
    print("\n" + "=" * 80)
    print("✅ OPTIMIZED PREDICTIONS COMPLETE")
    print("=" * 80)
    
    if len(optimized_picks) > 0:
        print(f"\n📁 Output files in outputs/:")
        print(f"   • ml_optimized_picks.xlsx - {len(optimized_picks)} optimized picks")
        print(f"   • ml_optimized_all_predictions.xlsx - {len(all_predictions)} predictions")
        print(f"   • ml_optimized_report.txt - Detailed analysis")
        print(f"\n💡 Expected win rate based on backtest: Review backtest_analysis_report.txt")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
