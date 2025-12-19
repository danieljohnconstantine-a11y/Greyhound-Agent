"""
Backtest Analysis Tool - Find Optimal Thresholds for 50%+ Win Rate

This script analyzes historical predictions against actual results to:
1. Test different ML confidence thresholds (50%, 55%, 60%, 65%, 70%)
2. Calculate win rates at each threshold level
3. Identify track-specific performance patterns
4. Recommend optimal settings for 50%+ win rate

Usage:
    python backtest_analyze.py

Prerequisites:
    1. Trained ML v2.1 model (models/greyhound_ml_v2.1_enhanced.pkl)
    2. Historical race PDFs in data/ folder
    3. Results CSVs in data/ folder (results_2025-*.csv)

Output:
    - Detailed analysis report in outputs/backtest_analysis_report.txt
    - Recommended threshold settings
    - Track-specific performance breakdowns
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.ml_predictor_advanced import AdvancedGreyhoundMLPredictor
from src.weather_track_data import WeatherTrackDataManager
from src.parser import parse_race_form
from src.features import compute_features
import pandas as pd
import numpy as np
import glob
import pdfplumber
from collections import defaultdict
from datetime import datetime

def load_results():
    """Load all historical results from CSV files"""
    results = {}
    csv_files = glob.glob("data/results_*.csv")
    loaded_count = 0
    error_count = 0
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            # Handle different CSV formats more robustly
            if 'Date' in df.columns and 'Race' in df.columns and 'Winner' in df.columns:
                # New format: Track,Date,Race,Winner
                for _, row in df.iterrows():
                    try:
                        key = (str(row['Track']).strip(), int(row['Race']))
                        results[key] = int(row['Winner'])
                        loaded_count += 1
                    except:
                        continue
            elif 'RaceNumber' in df.columns and 'WinnerBox' in df.columns:
                # Old format: Track,RaceNumber,WinnerBox
                for _, row in df.iterrows():
                    try:
                        key = (str(row['Track']).strip(), int(row['RaceNumber']))
                        results[key] = int(row['WinnerBox'])
                        loaded_count += 1
                    except:
                        continue
            elif 'Race' in df.columns and 'Winner' in df.columns:
                # Alternative format without Date
                for _, row in df.iterrows():
                    try:
                        key = (str(row['Track']).strip(), int(row['Race']))
                        results[key] = int(row['Winner'])
                        loaded_count += 1
                    except:
                        continue
            else:
                error_count += 1
                continue
        except Exception as e:
            error_count += 1
            continue
    
    if error_count > 0:
        print(f"⚠️  Skipped {error_count} CSV files with incompatible formats")
    
    return results

def parse_and_cache_pdfs(predictor, weather_manager, pdf_files):
    """
    Parse all PDFs once and cache the predictions
    This avoids reprocessing PDFs for every threshold test
    
    Returns:
        List of dicts with race predictions
    """
    print("\n📄 Parsing and caching all PDFs...")
    print(f"   Total PDFs to process: {len(pdf_files)}")
    print("   This may take 10-30 minutes depending on your system")
    
    all_predictions = []
    processed = 0
    errors = 0
    start_time = datetime.now()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        # Progress update every 10 PDFs
        if i % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            avg_per_pdf = elapsed / i
            remaining = (len(pdf_files) - i) * avg_per_pdf
            print(f"   Progress: {i}/{len(pdf_files)} PDFs ({i/len(pdf_files)*100:.1f}%) - "
                  f"Est. {remaining/60:.1f} min remaining")
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = "".join(page.extract_text() + "\n" for page in pdf.pages)
            
            df_dogs = parse_race_form(text)
            if df_dogs is None or len(df_dogs) == 0:
                continue
            
            df_dogs = compute_features(df_dogs)
            
            # Add weather features
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
            
            # Process each race in the PDF
            for (track, race_num), race_df in df_dogs.groupby(['Track', 'RaceNumber']):
                # Get ML predictions for this race
                ml_confidences = predictor.predict_confidence(race_df)
                
                # Create box to confidence mapping
                ml_predictions = {}
                for idx, row in race_df.iterrows():
                    try:
                        box_int = int(row['Box'])
                        ml_predictions[box_int] = ml_confidences.loc[idx] if idx in ml_confidences.index else 0
                    except:
                        continue
                
                if ml_predictions:
                    all_predictions.append({
                        'track': track,
                        'race_num': race_num,
                        'predictions': ml_predictions  # Dict of box -> confidence
                    })
            
            processed += 1
        
        except Exception as e:
            errors += 1
            continue
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n✅ Parsed {processed} PDFs successfully ({errors} errors)")
    print(f"   Total time: {elapsed/60:.1f} minutes")
    print(f"   Found {len(all_predictions)} races with predictions")
    
    return all_predictions

def test_threshold_from_cache(cached_predictions, results, threshold, min_confidence_spread=0):
    """
    Test prediction accuracy using cached predictions
    Much faster since PDFs are already parsed
    
    Args:
        cached_predictions: List of prediction dicts from parse_and_cache_pdfs
        results: Dict of (track, race) -> winner_box
        threshold: Minimum ML confidence percentage
        min_confidence_spread: Minimum lead over 2nd place (percentage points)
    
    Returns:
        Dict with performance metrics
    """
    total_picks = 0
    correct_picks = 0
    track_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    for pred in cached_predictions:
        track = pred['track']
        race_num = pred['race_num']
        ml_predictions = pred['predictions']
        
        # Find top prediction
        top_box = max(ml_predictions, key=ml_predictions.get)
        top_confidence = ml_predictions[top_box]
        
        # Check confidence spread if required
        if min_confidence_spread > 0:
            sorted_confs = sorted(ml_predictions.values(), reverse=True)
            if len(sorted_confs) > 1:
                spread = sorted_confs[0] - sorted_confs[1]
                if spread < min_confidence_spread:
                    continue  # Skip races without clear favorites
        
        # Only count predictions above threshold
        if top_confidence >= threshold:
            total_picks += 1
            
            # Check if we have result for this race
            result_key = (track, race_num)
            if result_key in results:
                actual_winner = results[result_key]
                if actual_winner == top_box:
                    correct_picks += 1
                    track_stats[track]['correct'] += 1
                track_stats[track]['total'] += 1
    
    win_rate = (correct_picks / total_picks * 100) if total_picks > 0 else 0
    
    return {
        'threshold': threshold,
        'min_spread': min_confidence_spread,
        'total_picks': total_picks,
        'correct_picks': correct_picks,
        'win_rate': win_rate,
        'track_stats': dict(track_stats)
    }

def main():
    print("=" * 80)
    print("🔍 BACKTEST ANALYSIS TOOL - Finding Optimal Thresholds")
    print("=" * 80)
    
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
        print("✅ Model loaded")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return 1
    
    # Initialize weather manager
    print("\n🌤️  Loading weather data...")
    try:
        weather_manager = WeatherTrackDataManager()
        print("✅ Weather data loaded")
    except Exception as e:
        print(f"⚠️  Warning: {e}")
        weather_manager = WeatherTrackDataManager()
    
    # Load results
    print("\n📊 Loading historical results...")
    results = load_results()
    print(f"✅ Loaded {len(results)} race results from CSV files")
    
    # Find PDFs
    print("\n📄 Finding historical race PDFs...")
    pdf_files = glob.glob("data/*form.pdf")
    print(f"✅ Found {len(pdf_files)} PDF files")
    
    # Parse and cache all PDFs once
    # This is the slow part - but we only do it once!
    cached_predictions = parse_and_cache_pdfs(predictor, weather_manager, pdf_files)
    
    if not cached_predictions:
        print("❌ No predictions generated from PDFs")
        return 1
    
    # Test different thresholds (now very fast using cached predictions)
    print("\n🧪 Testing different ML confidence thresholds...")
    print("   (Using cached predictions - this will be fast!)")
    print()
    
    thresholds_to_test = [50, 55, 60, 65, 70, 75]
    spread_values = [0, 5, 10]  # Minimum confidence spread requirements
    
    results_data = []
    
    for threshold in thresholds_to_test:
        for spread in spread_values:
            print(f"   Testing: Threshold={threshold}%, Min Spread={spread}%...", end='')
            result = test_threshold_from_cache(cached_predictions, results, threshold, spread)
            results_data.append(result)
            
            if result['total_picks'] > 0:
                print(f" Win Rate: {result['win_rate']:.1f}% ({result['correct_picks']}/{result['total_picks']} picks)")
            else:
                print(f" No picks made")
    
    # Generate report
    print("\n" + "=" * 80)
    print("📈 ANALYSIS RESULTS")
    print("=" * 80)
    
    try:
        report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("BACKTEST ANALYSIS REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("OBJECTIVE: Find threshold settings to achieve 50%+ win rate")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("THRESHOLD TESTING RESULTS")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Sort by win rate
    results_data.sort(key=lambda x: x['win_rate'], reverse=True)
    
    best_50_plus = [r for r in results_data if r['win_rate'] >= 50 and r['total_picks'] >= 10]
    
    if best_50_plus:
        report_lines.append("✅ CONFIGURATIONS ACHIEVING 50%+ WIN RATE:")
        report_lines.append("")
        for result in best_50_plus:
            report_lines.append(f"  Threshold: {result['threshold']}%, Min Spread: {result['min_spread']}%")
            report_lines.append(f"  Win Rate: {result['win_rate']:.1f}%")
            report_lines.append(f"  Picks: {result['correct_picks']}/{result['total_picks']}")
            report_lines.append(f"  Selectivity: ~{result['total_picks']/len(pdf_files):.1f} picks per PDF")
            report_lines.append("")
    else:
        report_lines.append("⚠️  No configuration achieved 50%+ win rate with 10+ picks")
        report_lines.append("")
        report_lines.append("CLOSEST RESULTS:")
        report_lines.append("")
        for result in results_data[:5]:
            if result['total_picks'] >= 5:
                report_lines.append(f"  Threshold: {result['threshold']}%, Min Spread: {result['min_spread']}%")
                report_lines.append(f"  Win Rate: {result['win_rate']:.1f}%")
                report_lines.append(f"  Picks: {result['correct_picks']}/{result['total_picks']}")
                report_lines.append("")
    
    report_lines.append("=" * 80)
    report_lines.append("ALL THRESHOLD RESULTS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"{'Threshold':<12} {'MinSpread':<12} {'Picks':<10} {'Wins':<10} {'Win Rate':<12}")
    report_lines.append("-" * 80)
    
    for result in results_data:
        if result['total_picks'] > 0:
            report_lines.append(f"{result['threshold']:<12} {result['min_spread']:<12} "
                              f"{result['total_picks']:<10} {result['correct_picks']:<10} "
                              f"{result['win_rate']:.1f}%")
    
    # Track-specific analysis for best configuration
    if results_data and results_data[0]['total_picks'] > 0:
        best = results_data[0]
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append(f"TRACK-SPECIFIC ANALYSIS (Best Config: {best['threshold']}%, Spread: {best['min_spread']}%)")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        if best['track_stats']:
            report_lines.append(f"{'Track':<30} {'Picks':<10} {'Wins':<10} {'Win Rate':<12}")
            report_lines.append("-" * 80)
            
            try:
                for track, stats in sorted(best['track_stats'].items(), 
                                           key=lambda x: (x[1]['correct']/x[1]['total'] if x[1]['total'] > 0 else 0), 
                                           reverse=True):
                    if stats['total'] > 0:
                        track_win_rate = stats['correct'] / stats['total'] * 100
                        report_lines.append(f"{track:<30} {stats['total']:<10} {stats['correct']:<10} {track_win_rate:.1f}%")
            except Exception as e:
                report_lines.append(f"Error generating track stats: {e}")
        else:
            report_lines.append("No track-specific data available")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("RECOMMENDATIONS")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    if best_50_plus:
        best_config = best_50_plus[0]
        report_lines.append(f"✅ RECOMMENDED CONFIGURATION:")
        report_lines.append(f"   ML Confidence Threshold: {best_config['threshold']}%")
        report_lines.append(f"   Minimum Confidence Spread: {best_config['min_spread']}%")
        report_lines.append(f"   Expected Win Rate: {best_config['win_rate']:.1f}%")
        report_lines.append(f"   Expected Picks per Day: ~{best_config['total_picks']/len(pdf_files):.1f}")
        report_lines.append("")
        report_lines.append("To use these settings, run:")
        report_lines.append(f"   python run_ml_optimized.py --threshold {best_config['threshold']} --min-spread {best_config['min_spread']}")
    else:
        report_lines.append("⚠️  Unable to achieve 50%+ win rate with current model and data.")
        report_lines.append("")
        report_lines.append("SUGGESTIONS:")
        report_lines.append("1. Retrain model with train_ml_enhanced.bat to use all 1,969 races")
        report_lines.append("2. Try ensemble methods (combine multiple algorithms)")
        report_lines.append("3. Focus on specific tracks with highest win rates")
        report_lines.append("4. Consider additional feature engineering")
        report_lines.append("")
        if results_data and results_data[0]['total_picks'] > 0:
            report_lines.append(f"Best current performance: {results_data[0]['win_rate']:.1f}% "
                              f"at {results_data[0]['threshold']}% threshold")
    
        report_lines.append("")
        report_lines.append("=" * 80)
        
        # Write report
        os.makedirs("outputs", exist_ok=True)
        report_file = "outputs/backtest_analysis_report.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        # Print to console
        for line in report_lines:
            print(line)
        
        print(f"\n✅ Full report saved to: {report_file}")
        print("\nNext step: Use run_ml_optimized.py with recommended settings")
        
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
