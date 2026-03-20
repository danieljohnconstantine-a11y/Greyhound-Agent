"""
Results Analysis Tool for Greyhound Racing Predictions

This module analyzes actual race results against predictions to:
1. Calculate prediction accuracy metrics
2. Identify which features correlate with winning
3. Optimize scoring weights using machine learning
4. Generate performance reports

Usage:
    python -m src.results_analyzer --results data/results.csv --predictions outputs/todays_form.csv
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import json
from pathlib import Path


def parse_box_results(results_text):
    """
    Parse race results from formatted text into structured data.
    
    Format:
    Track Name
    Date
    R1: 4,5,8,1  (box numbers in finishing order: 1st, 2nd, 3rd, 4th)
    R2: 1,6,4,8
    ...
    
    Returns:
        pd.DataFrame with columns: Track, RaceDate, RaceNumber, Box, FinishPosition
    """
    results = []
    current_track = None
    current_date = None
    
    lines = results_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a date line
        if any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June',
                                            'July', 'August', 'September', 'October', 'November', 'December']):
            # Parse date (e.g., "Saturday 22nd November 2025")
            parts = line.split()
            for i, part in enumerate(parts):
                if part in ['January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December']:
                    month = part
                    day = parts[i-1].rstrip('st').rstrip('nd').rstrip('rd').rstrip('th')
                    year = parts[i+1] if i+1 < len(parts) else '2025'
                    current_date = f"{year}-{month[:3]}-{day.zfill(2)}"
                    break
        
        # Check if it's a track name line
        elif not line.startswith('R') and not line.startswith('ALL') and current_date:
            current_track = line
        
        # Check if it's a race result line
        elif line.startswith('R'):
            # Format: "R1" or "R1: 4,5,8,1" or "R1\n4,5,8,1"
            if ':' in line:
                race_part, boxes_part = line.split(':', 1)
            else:
                race_part = line
                boxes_part = ""
            
            race_num = int(race_part[1:])  # Extract number after 'R'
            
            if boxes_part.strip():
                boxes = [int(b.strip()) for b in boxes_part.strip().split(',')]
                
                for position, box in enumerate(boxes, 1):
                    results.append({
                        'Track': current_track,
                        'RaceDate': current_date,
                        'RaceNumber': race_num,
                        'Box': box,
                        'FinishPosition': position
                    })
    
    return pd.DataFrame(results)


def parse_winner_results(results_text):
    """
    Parse race results from detailed format with winner names.
    
    Format:
    Track Name Race Results
    R1: RACE NAME | Distance | Winner: BOX. DOG NAME $odds | Time
    
    Returns:
        pd.DataFrame with columns: Track, RaceDate, RaceNumber, Box, DogName, Distance, Time
    """
    results = []
    current_track = None
    current_date = None
    
    lines = results_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Track name line
        if 'Race Results' in line:
            current_track = line.split('Race Results')[0].strip()
            continue
        
        # Date line with Weather info
        if '[' in line and 'Weather' in line:
            # Extract date from end of line
            if '2025-' in line or '2024-' in line:
                parts = line.split()
                for part in parts:
                    if '-' in part and len(part) == 10:  # YYYY-MM-DD format
                        current_date = part
                        break
            continue
        
        # Race result line (R1, R2, etc.)
        if line.startswith('R') and any(c.isdigit() for c in line[:3]):
            try:
                # Extract race number
                race_num_str = ''
                for char in line[1:]:
                    if char.isdigit():
                        race_num_str += char
                    else:
                        break
                
                if not race_num_str:
                    continue
                    
                race_num = int(race_num_str)
                
                # Look for distance (e.g., "342m", "520m")
                distance = None
                if '|' in line:
                    parts = line.split('|')
                    for part in parts:
                        if 'm' in part and any(c.isdigit() for c in part):
                            dist_str = ''.join(c for c in part if c.isdigit())
                            if dist_str:
                                distance = int(dist_str)
                                break
                
                # Look for winner box number (e.g., "2. BRISTOL MOSS")
                box = None
                for part in line.split():
                    if part.endswith('.') and part[:-1].isdigit():
                        box = int(part[:-1])
                        break
                
                if box and current_track:
                    results.append({
                        'Track': current_track,
                        'RaceDate': current_date or '2025-11-22',
                        'RaceNumber': race_num,
                        'Box': box,
                        'Distance': distance,
                        'FinishPosition': 1  # We only have winner info
                    })
            except (ValueError, IndexError):
                continue
    
    return pd.DataFrame(results)


def load_results(results_source):
    """
    Load race results from various sources.
    
    Args:
        results_source: Can be:
            - Path to CSV file
            - Path to text file with formatted results
            - String with formatted results
            
    Returns:
        pd.DataFrame with standardized columns
    """
    if isinstance(results_source, str):
        path = Path(results_source)
        if path.exists() and path.suffix == '.csv':
            return pd.read_csv(path)
        elif path.exists():
            with open(path, 'r') as f:
                text = f.read()
            # Try both parsers
            df1 = parse_box_results(text)
            df2 = parse_winner_results(text)
            return pd.concat([df1, df2], ignore_index=True) if not df2.empty else df1
        else:
            # Assume it's raw text
            df1 = parse_box_results(results_source)
            df2 = parse_winner_results(results_source)
            return pd.concat([df1, df2], ignore_index=True) if not df2.empty else df1
    elif isinstance(results_source, pd.DataFrame):
        return results_source
    else:
        raise ValueError("results_source must be a file path or DataFrame")


def match_predictions_with_results(predictions_df, results_df):
    """
    Match prediction data with actual race results.
    
    Args:
        predictions_df: DataFrame with predictions (from todays_form.csv)
        results_df: DataFrame with actual results
        
    Returns:
        pd.DataFrame with matched data including 'ActualWin' column
    """
    # Ensure consistent data types
    predictions_df = predictions_df.copy()
    results_df = results_df.copy()
    
    # Standardize track names (handle variations)
    def standardize_track(track):
        if pd.isna(track):
            return track
        track = str(track).upper().strip()
        # Handle common variations
        track_map = {
            'SANDOWN': 'SANDOWN PARK',
            'SANDOWN PK': 'SANDOWN PARK',
            'WENTWORTH': 'WENTWORTH PARK',
            'Q LAKESIDE': 'LAKESIDE',
            'ANGLE PK': 'ANGLE PARK',
        }
        return track_map.get(track, track)
    
    predictions_df['Track'] = predictions_df['Track'].apply(standardize_track)
    results_df['Track'] = results_df['Track'].apply(standardize_track)
    
    # Convert box and race numbers to integers
    predictions_df['Box'] = pd.to_numeric(predictions_df['Box'], errors='coerce').astype('Int64')
    predictions_df['RaceNumber'] = pd.to_numeric(predictions_df['RaceNumber'], errors='coerce').astype('Int64')
    results_df['Box'] = pd.to_numeric(results_df['Box'], errors='coerce').astype('Int64')
    results_df['RaceNumber'] = pd.to_numeric(results_df['RaceNumber'], errors='coerce').astype('Int64')
    
    # Merge on Track, RaceNumber, and Box
    merged = predictions_df.merge(
        results_df[['Track', 'RaceNumber', 'Box', 'FinishPosition']],
        on=['Track', 'RaceNumber', 'Box'],
        how='left'
    )
    
    # Create binary win indicator
    merged['ActualWin'] = (merged['FinishPosition'] == 1).astype(int)
    merged['ActualTop3'] = (merged['FinishPosition'] <= 3).fillna(False).astype(int)
    
    return merged


def calculate_accuracy_metrics(matched_df):
    """
    Calculate prediction accuracy metrics.
    
    Args:
        matched_df: DataFrame with predictions and actual results
        
    Returns:
        dict with accuracy metrics
    """
    # Filter to only races where we have results
    with_results = matched_df[matched_df['FinishPosition'].notna()].copy()
    
    if len(with_results) == 0:
        return {
            'total_races_analyzed': 0,
            'message': 'No matching results found'
        }
    
    # Group by race to get predictions per race
    races = with_results.groupby(['Track', 'RaceNumber'])
    
    metrics = {
        'total_races_analyzed': len(races),
        'total_dogs_analyzed': len(with_results),
        'races_with_winner_data': with_results['ActualWin'].sum(),
    }
    
    # Winner prediction accuracy
    top1_correct = 0
    top3_correct = 0
    
    for (track, race_num), group in races:
        # Sort by FinalScore to get our predictions
        group_sorted = group.sort_values('FinalScore', ascending=False)
        
        # Check if our #1 pick won
        if len(group_sorted) > 0 and group_sorted.iloc[0]['ActualWin'] == 1:
            top1_correct += 1
        
        # Check if actual winner is in our top 3
        if group_sorted.head(3)['ActualWin'].sum() > 0:
            top3_correct += 1
    
    metrics['winner_prediction_accuracy'] = top1_correct / len(races) if len(races) > 0 else 0
    metrics['top3_hit_rate'] = top3_correct / len(races) if len(races) > 0 else 0
    
    # Feature correlations with winning
    feature_cols = [
        'Speed_kmh', 'EarlySpeedIndex', 'ConsistencyIndex',
        'FinishConsistency', 'MarginAvg', 'FormMomentum',
        'RecentFormBoost', 'BoxBiasFactor', 'TrainerStrikeRate',
        'DistanceSuit', 'FinalScore'
    ]
    
    correlations = {}
    for col in feature_cols:
        if col in with_results.columns:
            # Remove NaN values for correlation
            valid_data = with_results[[col, 'ActualWin']].dropna()
            if len(valid_data) > 10:  # Need enough data points
                corr = valid_data[col].corr(valid_data['ActualWin'])
                correlations[col] = corr if not pd.isna(corr) else 0
    
    metrics['feature_correlations'] = correlations
    
    return metrics


def optimize_weights(matched_df):
    """
    Use machine learning to optimize feature weights.
    
    Args:
        matched_df: DataFrame with predictions and actual results
        
    Returns:
        dict with optimized weights
    """
    # Filter to races with results
    with_results = matched_df[matched_df['ActualWin'].notna()].copy()
    
    if len(with_results) < 50:
        return {
            'status': 'insufficient_data',
            'message': f'Need at least 50 races with results. Currently have {len(with_results)} dogs.',
            'recommended_weights': None
        }
    
    # Select features for optimization
    feature_cols = [
        'Speed_kmh', 'EarlySpeedIndex', 'ConsistencyIndex',
        'RecentFormBoost', 'BoxBiasFactor', 'TrainerStrikeRate'
    ]
    
    # Prepare data
    X = with_results[feature_cols].fillna(0)
    y = with_results['ActualWin']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y if y.sum() > 5 else None
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train logistic regression
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train_scaled, y_train)
    
    # Get feature importance (coefficients)
    coefficients = model.coef_[0]
    
    # Normalize to weights that sum to 1
    abs_coef = np.abs(coefficients)
    weights = abs_coef / abs_coef.sum()
    
    optimized_weights = dict(zip(feature_cols, weights))
    
    # Calculate accuracy
    train_accuracy = model.score(X_train_scaled, y_train)
    test_accuracy = model.score(X_test_scaled, y_test)
    
    return {
        'status': 'success',
        'optimized_weights': optimized_weights,
        'train_accuracy': train_accuracy,
        'test_accuracy': test_accuracy,
        'feature_importance': dict(zip(feature_cols, coefficients))
    }


def generate_report(metrics, optimization_results, output_path='outputs/results_analysis.txt'):
    """
    Generate a human-readable analysis report.
    
    Args:
        metrics: Accuracy metrics dictionary
        optimization_results: Weight optimization results
        output_path: Where to save the report
    """
    report = []
    report.append("=" * 80)
    report.append("GREYHOUND RACING PREDICTION ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Summary metrics
    report.append("PREDICTION ACCURACY SUMMARY")
    report.append("-" * 80)
    report.append(f"Total races analyzed: {metrics.get('total_races_analyzed', 0)}")
    report.append(f"Total dogs analyzed: {metrics.get('total_dogs_analyzed', 0)}")
    report.append(f"Winner prediction accuracy: {metrics.get('winner_prediction_accuracy', 0):.1%}")
    report.append(f"Top-3 hit rate: {metrics.get('top3_hit_rate', 0):.1%}")
    report.append("")
    
    # Feature correlations
    if 'feature_correlations' in metrics:
        report.append("FEATURE CORRELATION WITH WINNING")
        report.append("-" * 80)
        correlations = metrics['feature_correlations']
        sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        for feature, corr in sorted_corr:
            direction = "↑" if corr > 0 else "↓"
            report.append(f"{feature:.<40} {direction} {corr:>6.3f}")
        report.append("")
    
    # Optimization results
    if optimization_results.get('status') == 'success':
        report.append("OPTIMIZED FEATURE WEIGHTS")
        report.append("-" * 80)
        weights = optimization_results['optimized_weights']
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        for feature, weight in sorted_weights:
            report.append(f"{feature:.<40} {weight:>6.1%}")
        report.append("")
        report.append(f"Model training accuracy: {optimization_results['train_accuracy']:.1%}")
        report.append(f"Model testing accuracy: {optimization_results['test_accuracy']:.1%}")
    else:
        report.append("WEIGHT OPTIMIZATION")
        report.append("-" * 80)
        report.append(f"Status: {optimization_results.get('message', 'Not performed')}")
    
    report.append("")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    
    # Save to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    # Also print to console
    print(report_text)
    
    return report_text


def main():
    """
    Main function for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze greyhound race predictions against actual results')
    parser.add_argument('--results', required=True, help='Path to results file (CSV or text)')
    parser.add_argument('--predictions', default='outputs/todays_form.csv', help='Path to predictions CSV')
    parser.add_argument('--output', default='outputs/results_analysis.txt', help='Output report path')
    
    args = parser.parse_args()
    
    # Load data
    print("Loading results...")
    results_df = load_results(args.results)
    print(f"Loaded {len(results_df)} result records")
    
    print("Loading predictions...")
    predictions_df = pd.read_csv(args.predictions)
    print(f"Loaded {len(predictions_df)} predictions")
    
    # Match data
    print("Matching predictions with results...")
    matched_df = match_predictions_with_results(predictions_df, results_df)
    matched_count = matched_df['FinishPosition'].notna().sum()
    print(f"Matched {matched_count} predictions with results")
    
    # Calculate metrics
    print("Calculating accuracy metrics...")
    metrics = calculate_accuracy_metrics(matched_df)
    
    # Optimize weights
    print("Optimizing feature weights...")
    optimization = optimize_weights(matched_df)
    
    # Generate report
    print("Generating report...")
    generate_report(metrics, optimization, args.output)
    
    # Save matched data
    matched_output = args.output.replace('.txt', '_matched_data.csv')
    matched_df.to_csv(matched_output, index=False)
    print(f"\nMatched data saved to: {matched_output}")
    print(f"Analysis report saved to: {args.output}")


if __name__ == '__main__':
    main()
