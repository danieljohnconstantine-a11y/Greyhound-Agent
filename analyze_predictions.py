#!/usr/bin/env python3
"""
Analyze prediction accuracy for greyhound racing predictions.

This script:
1. Reads predicted runners from outputs/todays_form_color.xlsx
2. Accepts actual winners data
3. Compares predictions vs actuals
4. Calculates accuracy metrics
5. Analyzes scoring variables for correlation with winning picks
6. Recommends scoring adjustments
"""

import pandas as pd
import numpy as np
from scipy import stats
import sys
from datetime import datetime


# Constants
VARIANCE_THRESHOLD = 1e-10  # Threshold for detecting low variance
DEFAULT_ANALYSIS_DATE = '2024-11-25'  # Default date to analyze


# Current weights from src/features.py for reference
CURRENT_WEIGHTS = {
    'Sprint': {  # distance < 400
        "EarlySpeedIndex": 0.30,
        "Speed_kmh": 0.20,
        "ConsistencyIndex": 0.10,
        "FinishConsistency": 0.05,
        "PrizeMoney": 0.10,
        "RecentFormBoost": 0.10,
        "BoxBiasFactor": 0.10,
        "TrainerStrikeRate": 0.05,
        "DistanceSuit": 0.05,
        "TrackConditionAdj": 0.05
    },
    'Middle': {  # distance 400-500
        "EarlySpeedIndex": 0.25,
        "Speed_kmh": 0.20,
        "ConsistencyIndex": 0.15,
        "FinishConsistency": 0.05,
        "PrizeMoney": 0.10,
        "RecentFormBoost": 0.10,
        "BoxBiasFactor": 0.05,
        "TrainerStrikeRate": 0.05,
        "DistanceSuit": 0.05,
        "TrackConditionAdj": 0.05
    },
    'Long': {  # distance > 500
        "EarlySpeedIndex": 0.20,
        "Speed_kmh": 0.15,
        "ConsistencyIndex": 0.20,
        "FinishConsistency": 0.10,
        "PrizeMoney": 0.10,
        "RecentFormBoost": 0.10,
        "BoxBiasFactor": 0.05,
        "TrainerStrikeRate": 0.05,
        "DistanceSuit": 0.05,
        "TrackConditionAdj": 0.05
    }
}


def load_predictions(excel_path, analysis_date=None):
    """Load predictions from Excel file and identify top pick per race.
    
    Args:
        excel_path: Path to Excel file with predictions
        analysis_date: Date to filter for (defaults to DEFAULT_ANALYSIS_DATE)
    """
    df = pd.read_excel(excel_path)
    
    # Filter for specified date
    if analysis_date is None:
        analysis_date = DEFAULT_ANALYSIS_DATE
    
    df = df[df['RaceDate'] == analysis_date].copy()
    
    # Sort by Track, RaceNumber, and FinalScore (descending)
    df_sorted = df.sort_values(['Track', 'RaceNumber', 'FinalScore'], 
                               ascending=[True, True, False])
    
    # Get top prediction per race
    top_picks = df_sorted.groupby(['Track', 'RaceNumber']).first().reset_index()
    
    return df, top_picks


def parse_actual_winners(winners_input):
    """
    Parse actual winners from input string.
    
    Expected format (one per line):
    Track Name, R1, Box#
    Track Name, R2, Box#
    
    Or as a dictionary:
    {('Track Name', 1): box_number, ...}
    """
    if isinstance(winners_input, dict):
        return winners_input
    
    winners = {}
    lines = winners_input.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            track = parts[0]
            race_str = parts[1].upper().replace('R', '').strip()
            box_num = int(parts[2])
            
            race_num = int(race_str)
            winners[(track, race_num)] = box_num
    
    return winners


def compare_predictions(top_picks, actual_winners):
    """Compare predictions to actual winners and return results."""
    results = []
    
    for _, row in top_picks.iterrows():
        track = row['Track']
        race = row['RaceNumber']
        predicted_box = row['Box']
        
        actual_box = actual_winners.get((track, race))
        
        if actual_box is None:
            # No actual result for this race
            continue
        
        is_correct = (predicted_box == actual_box)
        
        results.append({
            'Track': track,
            'RaceNumber': race,
            'PredictedBox': predicted_box,
            'PredictedDog': row['DogName'],
            'ActualBox': actual_box,
            'Correct': is_correct,
            'PredictedScore': row['FinalScore']
        })
    
    return pd.DataFrame(results)


def analyze_scoring_variables(df_all, comparison_results):
    """
    Analyze which scoring variables correlate with correct predictions.
    
    For each scoring variable, compare distributions between correct and incorrect picks.
    """
    # Merge comparison results with full data
    df_analysis = df_all.merge(
        comparison_results[['Track', 'RaceNumber', 'Correct']],
        on=['Track', 'RaceNumber'],
        how='inner'
    )
    
    # Get only the top pick for each race (the one we actually predicted)
    df_analysis = df_analysis.sort_values(['Track', 'RaceNumber', 'FinalScore'], 
                                          ascending=[True, True, False])
    df_analysis = df_analysis.groupby(['Track', 'RaceNumber']).first().reset_index()
    
    # Scoring variables to analyze
    scoring_vars = [
        'EarlySpeedIndex', 'Speed_kmh', 'ConsistencyIndex', 
        'FinishConsistency', 'PrizeMoney', 'RecentFormBoost',
        'BoxBiasFactor', 'TrainerStrikeRate', 'DistanceSuit',
        'TrackConditionAdj', 'OverexposedPenalty', 'MarginAvg',
        'FormMomentum', 'PlaceRate', 'DLWFactor', 'WeightFactor',
        'DrawFactor', 'RTCFactor', 'BoxPositionBias', 'MarginFactor',
        'FormMomentumNorm'
    ]
    
    # Filter to only existing columns
    scoring_vars = [v for v in scoring_vars if v in df_analysis.columns]
    
    variable_analysis = []
    
    for var in scoring_vars:
        correct_vals = df_analysis[df_analysis['Correct'] == True][var].dropna()
        incorrect_vals = df_analysis[df_analysis['Correct'] == False][var].dropna()
        
        if len(correct_vals) == 0 or len(incorrect_vals) == 0:
            continue
        
        # Skip if no variance (all identical values)
        if correct_vals.std() < VARIANCE_THRESHOLD and incorrect_vals.std() < VARIANCE_THRESHOLD:
            continue
        
        # Calculate statistics
        correct_mean = correct_vals.mean()
        incorrect_mean = incorrect_vals.mean()
        correct_median = correct_vals.median()
        incorrect_median = incorrect_vals.median()
        correct_std = correct_vals.std()
        incorrect_std = incorrect_vals.std()
        
        # Calculate difference
        mean_diff = correct_mean - incorrect_mean
        median_diff = correct_median - incorrect_median
        
        # T-test for statistical significance
        try:
            # Skip if variance is too low (identical values)
            if correct_vals.std() < VARIANCE_THRESHOLD and incorrect_vals.std() < VARIANCE_THRESHOLD:
                t_stat, p_value = 0.0, 1.0
            else:
                t_stat, p_value = stats.ttest_ind(correct_vals, incorrect_vals, equal_var=False)
        except Exception as e:
            t_stat, p_value = np.nan, np.nan
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((correct_std**2 + incorrect_std**2) / 2)
        # Handle edge case where both groups have identical values
        if pooled_std < VARIANCE_THRESHOLD:
            cohens_d = 0.0
        else:
            cohens_d = mean_diff / pooled_std
        
        variable_analysis.append({
            'Variable': var,
            'Correct_Mean': correct_mean,
            'Incorrect_Mean': incorrect_mean,
            'Mean_Diff': mean_diff,
            'Correct_Median': correct_median,
            'Incorrect_Median': incorrect_median,
            'Median_Diff': median_diff,
            'Cohens_D': cohens_d,
            'P_Value': p_value,
            'Significant': p_value < 0.05 if not np.isnan(p_value) else False
        })
    
    return pd.DataFrame(variable_analysis).sort_values('Cohens_D', ascending=False, key=abs)


def generate_recommendations(variable_analysis, accuracy):
    """Generate recommendations for improving prediction accuracy."""
    recommendations = []
    
    # Find variables with strong positive correlation (high Cohen's d)
    strong_positive = variable_analysis[
        (variable_analysis['Cohens_D'] > 0.3) & 
        (variable_analysis['Significant'] == True)
    ].sort_values('Cohens_D', ascending=False)
    
    # Find variables with moderate positive correlation
    moderate_positive = variable_analysis[
        (variable_analysis['Cohens_D'] > 0.15) &
        (variable_analysis['Cohens_D'] <= 0.3) &
        (variable_analysis['Mean_Diff'] > 0)
    ].sort_values('Cohens_D', ascending=False)
    
    # Find variables with strong negative correlation (should decrease)
    strong_negative = variable_analysis[
        (variable_analysis['Cohens_D'] < -0.3) & 
        (variable_analysis['Significant'] == True)
    ].sort_values('Cohens_D', ascending=True)
    
    # Variables where higher values HURT predictions
    moderate_negative = variable_analysis[
        (variable_analysis['Cohens_D'] < -0.15) &
        (variable_analysis['Cohens_D'] >= -0.3) &
        (variable_analysis['Mean_Diff'] < 0)
    ].sort_values('Cohens_D', ascending=True)
    
    # Variables with no correlation
    weak_correlation = variable_analysis[
        (abs(variable_analysis['Cohens_D']) < 0.15)
    ]
    
    if len(strong_positive) > 0:
        recommendations.append({
            'type': 'INCREASE_WEIGHT',
            'priority': 'HIGH',
            'variables': strong_positive['Variable'].tolist(),
            'reason': 'These variables are significantly higher in correct predictions with strong effect',
            'effect_sizes': strong_positive['Cohens_D'].tolist(),
            'mean_diffs': strong_positive['Mean_Diff'].tolist()
        })
    
    if len(moderate_positive) > 0:
        recommendations.append({
            'type': 'INCREASE_WEIGHT',
            'priority': 'MEDIUM',
            'variables': moderate_positive['Variable'].tolist()[:5],
            'reason': 'These variables show moderate positive correlation with correct predictions',
            'effect_sizes': moderate_positive['Cohens_D'].tolist()[:5],
            'mean_diffs': moderate_positive['Mean_Diff'].tolist()[:5]
        })
    
    if len(strong_negative) > 0:
        recommendations.append({
            'type': 'DECREASE_WEIGHT',
            'priority': 'HIGH',
            'variables': strong_negative['Variable'].tolist(),
            'reason': 'These variables are significantly LOWER in correct predictions - high values hurt performance',
            'effect_sizes': strong_negative['Cohens_D'].tolist(),
            'mean_diffs': strong_negative['Mean_Diff'].tolist()
        })
    
    if len(moderate_negative) > 0:
        recommendations.append({
            'type': 'DECREASE_WEIGHT',
            'priority': 'MEDIUM',
            'variables': moderate_negative['Variable'].tolist()[:5],
            'reason': 'These variables show moderate negative correlation - higher values may hurt predictions',
            'effect_sizes': moderate_negative['Cohens_D'].tolist()[:5],
            'mean_diffs': moderate_negative['Mean_Diff'].tolist()[:5]
        })
    
    if len(weak_correlation) > 0:
        recommendations.append({
            'type': 'REMOVE_OR_REVISE',
            'priority': 'LOW',
            'variables': weak_correlation['Variable'].tolist()[:5],
            'reason': 'These variables show weak correlation with winning picks',
            'effect_sizes': weak_correlation['Cohens_D'].tolist()[:5],
            'mean_diffs': weak_correlation['Mean_Diff'].tolist()[:5]
        })
    
    return recommendations


def format_markdown_output(comparison_results, accuracy, variable_analysis, recommendations, df_all, analysis_date=None):
    """Format all results as Markdown for output."""
    
    if analysis_date is None:
        analysis_date = DEFAULT_ANALYSIS_DATE
    
    # Format date for display (convert YYYY-MM-DD to DD/MM/YYYY)
    try:
        date_obj = datetime.strptime(analysis_date, '%Y-%m-%d')
        display_date = date_obj.strftime('%d/%m/%Y')
    except:
        display_date = analysis_date
    
    correct_count = comparison_results['Correct'].sum()
    total_races = len(comparison_results)
    incorrect_count = total_races - correct_count
    
    md = f"""# 🏁 Greyhound Prediction Accuracy Analysis - {display_date}

## 📊 Overall Performance

- **Total Races Analyzed**: {total_races}
- **Correct Predictions**: {correct_count}
- **Incorrect Predictions**: {incorrect_count}
- **Prediction Accuracy**: **{accuracy:.2f}%**

## 🎯 Detailed Results by Track

"""
    
    # Group by track
    track_summary = comparison_results.groupby('Track').agg({
        'Correct': ['sum', 'count']
    }).reset_index()
    track_summary.columns = ['Track', 'Correct', 'Total']
    track_summary['Accuracy'] = (track_summary['Correct'] / track_summary['Total'] * 100).round(2)
    track_summary = track_summary.sort_values('Accuracy', ascending=False)
    
    md += "| Track | Correct | Total | Accuracy |\n"
    md += "|-------|---------|-------|----------|\n"
    for _, row in track_summary.iterrows():
        md += f"| {row['Track']} | {int(row['Correct'])} | {int(row['Total'])} | {row['Accuracy']:.1f}% |\n"
    
    md += "\n## 🔍 Scoring Variable Analysis\n\n"
    md += "**Top Variables Correlated with Correct Predictions:**\n\n"
    
    top_vars = variable_analysis.head(10)
    md += "| Variable | Correct Mean | Incorrect Mean | Difference | Effect Size (Cohen's d) | Significant |\n"
    md += "|----------|--------------|----------------|------------|------------------------|-------------|\n"
    
    for _, row in top_vars.iterrows():
        sig_marker = "✅" if row['Significant'] else "❌"
        md += f"| {row['Variable']} | {row['Correct_Mean']:.3f} | {row['Incorrect_Mean']:.3f} | "
        md += f"{row['Mean_Diff']:+.3f} | {row['Cohens_D']:.3f} | {sig_marker} |\n"
    
    md += "\n### 📈 Interpretation:\n"
    md += "- **Positive difference**: Variable is higher in correct predictions (should increase weight)\n"
    md += "- **Negative difference**: Variable is lower in correct predictions (should decrease weight)\n"
    md += "- **Effect Size > 0.3**: Meaningful difference\n"
    md += "- **Significance**: p-value < 0.05 indicates statistical significance\n"
    
    md += "\n## 💡 Recommendations\n\n"
    
    for i, rec in enumerate(recommendations, 1):
        priority_emoji = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
        md += f"### {i}. {priority_emoji} {rec['type'].replace('_', ' ').title()} (Priority: {rec['priority']})\n\n"
        
        md += f"**Variables**: {', '.join(rec['variables'])}\n\n"
        md += f"**Reason**: {rec['reason']}\n\n"
        
        # Show the specific differences
        for j, var in enumerate(rec['variables'][:3]):  # Limit to top 3 for readability
            if j < len(rec['mean_diffs']):
                md += f"  - `{var}`: Mean difference = {rec['mean_diffs'][j]:+.3f}, Effect size = {rec['effect_sizes'][j]:.3f}\n"
        md += "\n"
        
        if rec['type'] == 'INCREASE_WEIGHT':
            md += "**Action**: Increase the weights for these variables in the scoring algorithm "
            md += f"(in `src/features.py`, function `get_weights()`). "
            if rec['priority'] == 'HIGH':
                md += "These have the strongest correlation with winning picks.\n\n"
            else:
                md += "These show moderate positive correlation.\n\n"
        elif rec['type'] == 'DECREASE_WEIGHT':
            md += "**Action**: Decrease the weights for these variables or investigate why "
            md += "high values correlate with incorrect predictions. "
            if rec['priority'] == 'HIGH':
                md += "Winners tend to have LOWER values for these variables.\n\n"
            else:
                md += "Moderate negative correlation suggests caution.\n\n"
        else:
            md += "**Action**: Consider removing these variables or collecting better data for them, "
            md += "as they don't seem to contribute meaningfully to prediction accuracy.\n\n"
    
    # Add concrete weight recommendations
    md += "\n## ⚙️ Suggested Weight Adjustments\n\n"
    md += "Based on the analysis above, here are concrete weight adjustments for `src/features.py`:\n\n"
    
    # Collect all variables that need adjustment
    increase_vars = []
    decrease_vars = []
    
    for rec in recommendations:
        if rec['type'] == 'INCREASE_WEIGHT':
            for i, var in enumerate(rec['variables'][:3]):
                if i < len(rec['effect_sizes']):
                    increase_vars.append((var, rec['effect_sizes'][i], rec['priority']))
        elif rec['type'] == 'DECREASE_WEIGHT':
            for i, var in enumerate(rec['variables'][:3]):
                if i < len(rec['effect_sizes']):
                    decrease_vars.append((var, rec['effect_sizes'][i], rec['priority']))
    
    if increase_vars:
        md += "### Variables to INCREASE:\n\n"
        for var, effect, priority in increase_vars:
            adjustment = "strong" if priority == 'HIGH' else "moderate"
            md += f"- **{var}**: {adjustment} increase (effect size: {effect:.3f})\n"
        md += "\n"
    
    if decrease_vars:
        md += "### Variables to DECREASE:\n\n"
        for var, effect, priority in decrease_vars:
            adjustment = "strong" if priority == 'HIGH' else "moderate"
            md += f"- **{var}**: {adjustment} decrease (effect size: {effect:.3f})\n"
        md += "\n"
    
    md += "**Note**: Adjust weights proportionally while maintaining total weight = 1.0 for each distance category.\n\n"
    
    md += "\n## 🎲 Sample Predictions vs Actuals\n\n"
    
    # Show first 10 races
    sample = comparison_results.head(10)
    md += "| Track | Race | Predicted (Box) | Predicted Dog | Actual Box | Result |\n"
    md += "|-------|------|----------------|---------------|------------|--------|\n"
    
    for _, row in sample.iterrows():
        result = "✅ Correct" if row['Correct'] else "❌ Wrong"
        md += f"| {row['Track']} | R{row['RaceNumber']} | Box {row['PredictedBox']} | "
        md += f"{row['PredictedDog']} | Box {row['ActualBox']} | {result} |\n"
    
    if len(comparison_results) > 10:
        md += f"\n*... and {len(comparison_results) - 10} more races*\n"
    
    # Add summary statistics - merge df_analysis with comparison results
    df_with_results = df_all.merge(
        comparison_results[['Track', 'RaceNumber', 'Correct', 'PredictedBox']],
        on=['Track', 'RaceNumber'],
        how='inner'
    )
    # Get only the predicted dogs (top picks)
    df_with_results = df_with_results[df_with_results['Box'] == df_with_results['PredictedBox']]
    
    md += f"\n## 📈 Key Insights\n\n"
    
    # Check if certain distances perform better
    if 'Distance' in df_with_results.columns and len(df_with_results) > 0:
        md += "### Distance Analysis\n\n"
        df_dist = df_with_results.copy()
        df_dist['DistanceCategory'] = pd.cut(
            df_dist['Distance'], 
            bins=[0, 400, 500, 1000],
            labels=['Sprint (<400m)', 'Middle (400-500m)', 'Long (>500m)']
        )
        dist_accuracy = df_dist.groupby('DistanceCategory', observed=False)['Correct'].agg(['sum', 'count'])
        dist_accuracy['Accuracy'] = (dist_accuracy['sum'] / dist_accuracy['count'] * 100).round(1)
        
        md += "| Distance Category | Correct | Total | Accuracy |\n"
        md += "|-------------------|---------|-------|----------|\n"
        for cat, row in dist_accuracy.iterrows():
            md += f"| {cat} | {int(row['sum'])} | {int(row['count'])} | {row['Accuracy']:.1f}% |\n"
        md += "\n"
    
    return md


def main(winners_data=None, analysis_date=None):
    """Main analysis function.
    
    Args:
        winners_data: Optional dict or string of actual winners.
                     If None, will prompt for input or use command line args.
        analysis_date: Optional date string (YYYY-MM-DD) to analyze.
                      Defaults to DEFAULT_ANALYSIS_DATE.
    """
    
    if analysis_date is None:
        analysis_date = DEFAULT_ANALYSIS_DATE
    
    print("🔍 Loading predictions from outputs/todays_form_color.xlsx...")
    
    # Load predictions
    df_all, top_picks = load_predictions('outputs/todays_form_color.xlsx', analysis_date)
    
    print(f"✅ Loaded {len(top_picks)} races with predictions")
    print(f"   Tracks: {', '.join(top_picks['Track'].unique())}")
    
    # Determine source of actual winners
    if winners_data is not None:
        # Provided as function argument
        if isinstance(winners_data, str):
            actual_winners = parse_actual_winners(winners_data)
        else:
            actual_winners = winners_data
    elif len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            winners_input = f.read()
        actual_winners = parse_actual_winners(winners_input)
    else:
        # Interactive mode or example data
        print("\n" + "="*60)
        print("ACTUAL WINNERS DATA NEEDED")
        print("="*60)
        print("\nPlease provide actual winners in the format:")
        print("Track Name, R1, Box#")
        print("Track Name, R2, Box#")
        print("...")
        print("\nYou can either:")
        print("1. Pass a file path as argument: python analyze_predictions.py winners.txt")
        print("2. Enter data interactively below (press Ctrl+D when done):")
        print()
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        winners_input = '\n'.join(lines)
        actual_winners = parse_actual_winners(winners_input)
    
    if not actual_winners:
        print("\n❌ No actual winners data provided. Exiting.")
        return None
    
    print(f"\n✅ Loaded {len(actual_winners)} actual race results")
    
    # Compare predictions to actuals
    comparison_results = compare_predictions(top_picks, actual_winners)
    
    if len(comparison_results) == 0:
        print("\n❌ No matching races found between predictions and actuals.")
        return
    
    # Calculate accuracy
    correct_count = comparison_results['Correct'].sum()
    total_races = len(comparison_results)
    accuracy = (correct_count / total_races) * 100
    
    print(f"\n📊 Accuracy: {correct_count}/{total_races} = {accuracy:.2f}%")
    
    # Analyze scoring variables
    print("\n🔬 Analyzing scoring variables...")
    variable_analysis = analyze_scoring_variables(df_all, comparison_results)
    
    # Generate recommendations
    print("💡 Generating recommendations...")
    recommendations = generate_recommendations(variable_analysis, accuracy)
    
    # Format output
    markdown_output = format_markdown_output(
        comparison_results, 
        accuracy, 
        variable_analysis, 
        recommendations,
        df_all,
        analysis_date
    )
    
    # Print to console
    print("\n" + "="*60)
    print(markdown_output)
    print("="*60)
    
    # Save to file
    # Generate filename from analysis date
    date_str = analysis_date.replace('-', '')
    output_file = f'outputs/prediction_analysis_{date_str}.md'
    with open(output_file, 'w') as f:
        f.write(markdown_output)
    
    print(f"\n📄 Analysis saved to: {output_file}")
    
    # Also save detailed comparison results
    comparison_file = f'outputs/prediction_comparison_{date_str}.csv'
    comparison_results.to_csv(comparison_file, index=False)
    print(f"📄 Detailed comparison saved to: {comparison_file}")
    
    return markdown_output


if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("""
Greyhound Prediction Accuracy Analysis
======================================

Usage:
  python analyze_predictions.py [winners_file]
  python analyze_predictions.py -h|--help

Arguments:
  winners_file    Optional file containing actual race winners
                  Format: Track Name, R#, Box#
                  
Examples:
  python analyze_predictions.py actual_winners.txt
  python analyze_predictions.py example_winners.txt
  
If no file is provided, you can enter data interactively.
        """)
        sys.exit(0)
    
    main()


# Example usage in Python:
# from analyze_predictions import main
# 
# actual_winners = {
#     ('Angle Park', 1): 3,
#     ('Angle Park', 2): 7,
#     # ... etc
# }
# 
# result = main(winners_data=actual_winners)
