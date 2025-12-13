#!/usr/bin/env python3
"""
Speed Matrix Analysis and Optimization
Analyzes actual race results to optimize the speed matrix weights
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Configuration
OUTPUTS_DIR = Path("outputs")
DATA_FILE = OUTPUTS_DIR / "todays_form_color.xlsx"
WINNER_DATA_FILE = OUTPUTS_DIR / "actual_winners_25_11_25.csv"

# Normalization constants
# PrizeMoney normalization threshold - adjust based on racing jurisdiction
# For Australian racing, typical prize pools range from $1k-$500k
PRIZE_MONEY_DIVISOR = 1000  # Convert to thousands for better scaling

# All numeric variables used in scoring
SCORE_VARIABLES = [
    'Speed_kmh',
    'EarlySpeedIndex',
    'FinishConsistency',
    'MarginAvg',
    'FormMomentum',
    'ConsistencyIndex',
    'RecentFormBoost',
    'BoxBiasFactor',
    'TrainerStrikeRate',
    'DistanceSuit',
    'RestFactor',
    'OverexposedPenalty',
    'PlaceRate',
    'DLWFactor',
    'WeightFactor',
    'DrawFactor',
    'FormMomentumNorm',
    'MarginFactor',
    'RTCFactor',
    'BoxPositionBias',
    'PrizeMoney',
    'CareerWins',
    'CareerPlaces',
    'CareerStarts',
    'DLR',
    'DLW'
]


def load_data():
    """Load the form data"""
    print(f"Loading data from {DATA_FILE}...")
    df = pd.read_excel(DATA_FILE)
    print(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    return df


def create_sample_winner_data(df):
    """
    Create sample winner data file template
    This should be replaced with actual winner data
    """
    print("\nCreating sample winner data template...")
    
    # Group by race
    races = df.groupby(['Track', 'RaceNumber']).first().reset_index()
    
    winner_template = pd.DataFrame({
        'Track': races['Track'],
        'RaceNumber': races['RaceNumber'],
        'RaceDate': races['RaceDate'],
        'WinningBox': 0,  # To be filled with actual data
        'WinningDog': '',  # To be filled with actual data
    })
    
    template_file = OUTPUTS_DIR / "winner_data_template.csv"
    winner_template.to_csv(template_file, index=False)
    print(f"Template saved to {template_file}")
    print("Please fill in WinningBox and WinningDog columns with actual results")
    
    return winner_template


def load_or_create_winner_data(df):
    """Load actual winner data or create template"""
    if WINNER_DATA_FILE.exists():
        print(f"\nLoading actual winner data from {WINNER_DATA_FILE}...")
        winners = pd.read_csv(WINNER_DATA_FILE)
        return winners
    else:
        print("\n" + "!" * 80)
        print("WARNING: ACTUAL WINNER DATA NOT FOUND")
        print("!" * 80)
        print(f"\nWinner data file not found: {WINNER_DATA_FILE}")
        print("\nCreating template with SIMULATED (randomized) winners for demonstration...")
        print("\n*** IMPORTANT: Results with simulated data are NOT RELIABLE ***")
        print("*** For production use, you MUST provide actual race results ***")
        print("\nNOTE: For accurate results, please provide actual winner data!")
        print("!" * 80)
        
        # For demonstration, pick random winners with some bias toward higher scores
        # This simulates more realistic results
        winners_list = []
        np.random.seed(42)  # For reproducibility
        
        # Calculate max score range for normalization
        max_score = df['FinalScore'].max()
        min_score = df['FinalScore'].min()
        score_range = max_score - min_score if max_score > min_score else 1.0
        
        for (track, race_num), group in df.groupby(['Track', 'RaceNumber']):
            # Sort by score and add randomness
            group = group.copy()
            group['random_factor'] = np.random.random(len(group))
            # Weight: 70% score (normalized), 30% random (normalized to same scale)
            # Normalize FinalScore to 0-1 range, then scale random to match
            normalized_score = (group['FinalScore'] - min_score) / score_range
            group['weighted_score'] = normalized_score * 0.7 + group['random_factor'] * 0.3
            
            winner = group.nlargest(1, 'weighted_score').iloc[0]
            winners_list.append({
                'Track': track,
                'RaceNumber': race_num,
                'RaceDate': winner['RaceDate'],
                'WinningBox': winner['Box'],
                'WinningDog': winner['DogName']
            })
        
        winners = pd.DataFrame(winners_list)
        # Save as template
        template_file = OUTPUTS_DIR / "winner_data_template.csv"
        winners.to_csv(template_file, index=False)
        print(f"Template with simulated data saved to {template_file}")
        print(f"Replace this file with actual winner data and rename to: {WINNER_DATA_FILE.name}")
        
        return winners


def tag_winners(df, winners):
    """Tag actual winners in the dataset"""
    print("\nTagging actual winners...")
    
    # Merge winner data
    df = df.copy()
    df['IsWinner'] = False
    
    for _, winner_row in winners.iterrows():
        mask = (
            (df['Track'] == winner_row['Track']) &
            (df['RaceNumber'] == winner_row['RaceNumber']) &
            (df['Box'] == winner_row['WinningBox'])
        )
        df.loc[mask, 'IsWinner'] = True
    
    winner_count = df['IsWinner'].sum()
    print(f"Tagged {winner_count} winners out of {len(df)} total runners")
    
    return df


def calculate_separation_stats(df, variables):
    """Calculate winner vs non-winner separation for each variable"""
    print("\nCalculating winner separation statistics...")
    
    stats = []
    
    for var in variables:
        if var not in df.columns:
            print(f"  Warning: Variable {var} not found in dataset, skipping")
            continue
        
        # Get values for winners and non-winners
        winner_vals = df[df['IsWinner'] == True][var]
        non_winner_vals = df[df['IsWinner'] == False][var]
        
        # Handle non-numeric or missing data
        try:
            winner_vals = pd.to_numeric(winner_vals, errors='coerce').dropna()
            non_winner_vals = pd.to_numeric(non_winner_vals, errors='coerce').dropna()
            
            if len(winner_vals) == 0 or len(non_winner_vals) == 0:
                continue
            
            # Calculate statistics
            winner_mean = winner_vals.mean()
            winner_median = winner_vals.median()
            winner_std = winner_vals.std()
            
            non_winner_mean = non_winner_vals.mean()
            non_winner_median = non_winner_vals.median()
            non_winner_std = non_winner_vals.std()
            
            # Calculate separation metrics
            mean_diff = abs(winner_mean - non_winner_mean)
            median_diff = abs(winner_median - non_winner_median)
            
            # Normalized separation (Cohen's d effect size)
            pooled_std = np.sqrt((winner_std**2 + non_winner_std**2) / 2)
            if pooled_std > 0:
                cohens_d = mean_diff / pooled_std
            else:
                cohens_d = 0
            
            # Relative mean difference (as percentage)
            if non_winner_mean != 0:
                relative_diff = (mean_diff / abs(non_winner_mean)) * 100
            else:
                relative_diff = 0
            
            stats.append({
                'Variable': var,
                'Winner_Mean': winner_mean,
                'Winner_Median': winner_median,
                'Winner_Std': winner_std,
                'NonWinner_Mean': non_winner_mean,
                'NonWinner_Median': non_winner_median,
                'NonWinner_Std': non_winner_std,
                'Mean_Difference': mean_diff,
                'Median_Difference': median_diff,
                'Cohens_D': cohens_d,
                'Relative_Diff_Pct': relative_diff,
                'Winner_Count': len(winner_vals),
                'NonWinner_Count': len(non_winner_vals)
            })
            
        except Exception as e:
            print(f"  Error processing {var}: {e}")
            continue
    
    stats_df = pd.DataFrame(stats)
    
    # Sort by Cohen's D (effect size) descending
    stats_df = stats_df.sort_values('Cohens_D', ascending=False)
    
    print(f"Calculated separation stats for {len(stats_df)} variables")
    
    return stats_df


def calculate_dynamic_weights(stats_df, method='cohens_d'):
    """
    Calculate dynamic weights based on winner separation
    
    Args:
        stats_df: DataFrame with separation statistics
        method: 'cohens_d', 'mean_diff', or 'relative_diff'
    """
    print(f"\nCalculating dynamic weights using method: {method}...")
    
    # Select the metric to use for weighting
    if method == 'cohens_d':
        metric_col = 'Cohens_D'
    elif method == 'mean_diff':
        metric_col = 'Mean_Difference'
    elif method == 'relative_diff':
        metric_col = 'Relative_Diff_Pct'
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Get absolute values and handle negative values
    weights = stats_df[metric_col].abs()
    
    # Filter out very small values (negligible impact)
    weights = weights.where(weights > 0.01, 0)
    
    # Normalize to sum to 100%
    total = weights.sum()
    if total > 0:
        weights = (weights / total) * 100
    else:
        # If all weights are zero, distribute evenly
        weights = pd.Series([100.0 / len(weights)] * len(weights), index=weights.index)
    
    # Create weight matrix
    weight_matrix = pd.DataFrame({
        'Variable': stats_df['Variable'],
        'Weight_Percentage': weights.values,
        'Separation_Score': stats_df[metric_col].values
    })
    
    # Sort by weight descending
    weight_matrix = weight_matrix.sort_values('Weight_Percentage', ascending=False)
    
    print(f"Total weight: {weight_matrix['Weight_Percentage'].sum():.2f}%")
    print(f"\nTop 10 variables by weight:")
    print(weight_matrix.head(10).to_string(index=False))
    
    return weight_matrix


def apply_new_weights(df, weight_matrix):
    """Apply new speed matrix weights to calculate new scores"""
    print("\nApplying new weight matrix to calculate scores...")
    
    df = df.copy()
    
    # Create weight dictionary
    weights = dict(zip(weight_matrix['Variable'], weight_matrix['Weight_Percentage'] / 100))
    
    # Calculate new score
    new_scores = []
    for _, row in df.iterrows():
        score = 0
        for var, weight in weights.items():
            if var in df.columns and pd.notna(row[var]):
                try:
                    value = float(row[var])
                    # Normalize large values (like PrizeMoney) using configured divisor
                    if var == 'PrizeMoney' and value > PRIZE_MONEY_DIVISOR:
                        value = value / PRIZE_MONEY_DIVISOR
                    score += value * weight
                except:
                    pass
        new_scores.append(score)
    
    df['NewFinalScore'] = new_scores
    
    print(f"Calculated new scores for {len(df)} runners")
    print(f"Score range: {df['NewFinalScore'].min():.2f} to {df['NewFinalScore'].max():.2f}")
    
    return df


def evaluate_predictions(df):
    """Evaluate how well predictions match actual winners"""
    print("\nEvaluating prediction accuracy...")
    
    results = {
        'old_picks': {'correct': 0, 'total': 0, 'races': 0},
        'new_picks': {'correct': 0, 'total': 0, 'races': 0}
    }
    
    # Evaluate per race
    for (track, race_num), group in df.groupby(['Track', 'RaceNumber']):
        results['old_picks']['races'] += 1
        results['new_picks']['races'] += 1
        
        # Old prediction (top scorer by FinalScore)
        old_top = group.nlargest(1, 'FinalScore').iloc[0]
        if old_top['IsWinner']:
            results['old_picks']['correct'] += 1
        results['old_picks']['total'] += 1
        
        # New prediction (top scorer by NewFinalScore)
        new_top = group.nlargest(1, 'NewFinalScore').iloc[0]
        if new_top['IsWinner']:
            results['new_picks']['correct'] += 1
        results['new_picks']['total'] += 1
    
    # Calculate percentages
    old_pct = (results['old_picks']['correct'] / results['old_picks']['total'] * 100) if results['old_picks']['total'] > 0 else 0
    new_pct = (results['new_picks']['correct'] / results['new_picks']['total'] * 100) if results['new_picks']['total'] > 0 else 0
    
    print(f"\nPrediction Accuracy:")
    print(f"  Old Speed Matrix: {results['old_picks']['correct']}/{results['old_picks']['total']} winners picked ({old_pct:.1f}%)")
    print(f"  New Speed Matrix: {results['new_picks']['correct']}/{results['new_picks']['total']} winners picked ({new_pct:.1f}%)")
    print(f"  Improvement: {new_pct - old_pct:+.1f} percentage points")
    
    return results


def generate_summary_report(stats_df, weight_matrix, results, df):
    """Generate comprehensive summary report"""
    print("\nGenerating summary report...")
    
    report = {
        'analysis_date': datetime.now().isoformat(),
        'race_date': '2024-11-25',
        'total_races': int(len(df.groupby(['Track', 'RaceNumber']))),
        'total_runners': int(len(df)),
        'total_winners': int(df['IsWinner'].sum()),
        
        'prediction_accuracy': {
            'old_speed_matrix': {
                'winners_picked': int(results['old_picks']['correct']),
                'total_races': int(results['old_picks']['total']),
                'accuracy_percentage': float(round((results['old_picks']['correct'] / results['old_picks']['total'] * 100) if results['old_picks']['total'] > 0 else 0, 2))
            },
            'new_speed_matrix': {
                'winners_picked': int(results['new_picks']['correct']),
                'total_races': int(results['new_picks']['total']),
                'accuracy_percentage': float(round((results['new_picks']['correct'] / results['new_picks']['total'] * 100) if results['new_picks']['total'] > 0 else 0, 2))
            },
            'improvement': {
                'additional_winners': int(results['new_picks']['correct'] - results['old_picks']['correct']),
                'percentage_point_change': float(round((results['new_picks']['correct'] / results['new_picks']['total'] * 100) - (results['old_picks']['correct'] / results['old_picks']['total'] * 100) if results['old_picks']['total'] > 0 else 0, 2))
            }
        },
        
        'top_10_variables': [
            {k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
             for k, v in record.items()} 
            for record in weight_matrix.head(10).to_dict('records')
        ],
        
        'statistics_summary': {
            'variables_analyzed': int(len(stats_df)),
            'highest_separation_variable': str(stats_df.iloc[0]['Variable']) if len(stats_df) > 0 else None,
            'highest_cohens_d': float(round(stats_df.iloc[0]['Cohens_D'], 3)) if len(stats_df) > 0 else None
        }
    }
    
    # Save JSON report
    report_file = OUTPUTS_DIR / "speed_matrix_analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"JSON report saved to {report_file}")
    
    # Save text summary
    summary_file = OUTPUTS_DIR / "speed_matrix_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SPEED MATRIX ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Analysis Date: {report['analysis_date']}\n")
        f.write(f"Race Date: {report['race_date']}\n")
        f.write(f"Total Races: {report['total_races']}\n")
        f.write(f"Total Runners: {report['total_runners']}\n")
        f.write(f"Total Winners Tagged: {report['total_winners']}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("PREDICTION ACCURACY\n")
        f.write("-" * 80 + "\n\n")
        
        old_acc = report['prediction_accuracy']['old_speed_matrix']
        new_acc = report['prediction_accuracy']['new_speed_matrix']
        imp = report['prediction_accuracy']['improvement']
        
        f.write(f"Old Speed Matrix:\n")
        f.write(f"  Winners Picked: {old_acc['winners_picked']}/{old_acc['total_races']}\n")
        f.write(f"  Accuracy: {old_acc['accuracy_percentage']}%\n\n")
        
        f.write(f"New Speed Matrix:\n")
        f.write(f"  Winners Picked: {new_acc['winners_picked']}/{new_acc['total_races']}\n")
        f.write(f"  Accuracy: {new_acc['accuracy_percentage']}%\n\n")
        
        f.write(f"Improvement:\n")
        f.write(f"  Additional Winners: {imp['additional_winners']:+d}\n")
        f.write(f"  Percentage Point Change: {imp['percentage_point_change']:+.2f}pp\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("TOP 10 WEIGHTED VARIABLES\n")
        f.write("-" * 80 + "\n\n")
        
        for i, var in enumerate(report['top_10_variables'], 1):
            f.write(f"{i:2d}. {var['Variable']:25s} - {var['Weight_Percentage']:5.2f}% (separation: {var['Separation_Score']:.3f})\n")
        
        f.write("\n" + "=" * 80 + "\n")
    
    print(f"Text summary saved to {summary_file}")
    
    return report


def main():
    """Main analysis workflow"""
    print("=" * 80)
    print("SPEED MATRIX ANALYSIS AND OPTIMIZATION")
    print("=" * 80)
    
    # Load data
    df = load_data()
    
    # Load or create winner data
    winners = load_or_create_winner_data(df)
    
    # Tag winners
    df = tag_winners(df, winners)
    
    # Calculate separation statistics
    stats_df = calculate_separation_stats(df, SCORE_VARIABLES)
    
    # Save separation statistics
    stats_file = OUTPUTS_DIR / "variable_separation_stats.csv"
    stats_df.to_csv(stats_file, index=False)
    print(f"\nSeparation statistics saved to {stats_file}")
    
    # Calculate dynamic weights
    weight_matrix = calculate_dynamic_weights(stats_df, method='cohens_d')
    
    # Save weight matrix
    weights_file = OUTPUTS_DIR / "new_speed_matrix_weights.csv"
    weight_matrix.to_csv(weights_file, index=False)
    print(f"\nWeight matrix saved to {weights_file}")
    
    # Apply new weights
    df = apply_new_weights(df, weight_matrix)
    
    # Save updated predictions
    predictions_file = OUTPUTS_DIR / "predictions_with_new_matrix.csv"
    df.to_csv(predictions_file, index=False)
    print(f"Updated predictions saved to {predictions_file}")
    
    # Evaluate predictions
    results = evaluate_predictions(df)
    
    # Generate summary report
    report = generate_summary_report(stats_df, weight_matrix, results, df)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nKey Outputs:")
    print(f"  1. Variable Separation Stats: {stats_file}")
    print(f"  2. New Weight Matrix: {weights_file}")
    print(f"  3. Updated Predictions: {predictions_file}")
    print(f"  4. JSON Report: {OUTPUTS_DIR / 'speed_matrix_analysis_report.json'}")
    print(f"  5. Summary: {OUTPUTS_DIR / 'speed_matrix_summary.txt'}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
