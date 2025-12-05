# Prediction Accuracy Analysis

This script analyzes the accuracy of greyhound racing predictions against actual race results.

## Usage

### Option 1: With Actual Winners File

Create a text file with actual winners in the format:
```
Track Name, R1, Box#
Track Name, R2, Box#
...
```

Then run:
```bash
python analyze_predictions.py actual_winners.txt
```

### Option 2: Interactive Mode

Run the script without arguments and enter winners interactively:
```bash
python analyze_predictions.py
```

Then paste your actual winners data and press Ctrl+D when done.

### Option 3: Programmatic Usage

```python
from analyze_predictions import main

actual_winners = {
    ('Angle Park', 1): 3,
    ('Angle Park', 2): 5,
    # ... etc
}

result = main(winners_data=actual_winners)
```

## Example

An example winners file (`example_winners.txt`) is provided for demonstration:

```bash
python analyze_predictions.py example_winners.txt
```

## Output

The script will:
1. Calculate overall prediction accuracy
2. Show accuracy by track
3. Analyze which scoring variables correlate with correct predictions
4. Provide prioritized recommendations for adjusting scoring weights
5. Save results to `outputs/prediction_analysis_25nov2024.md`

## Input Data

- **Predictions**: Read from `outputs/todays_form_color.xlsx`
- **Actual Winners**: Provided by user (track name, race number, box number)

## Analysis Features

- Statistical significance testing (t-tests)
- Effect size calculation (Cohen's d)
- Distribution analysis for each scoring variable
- Distance-based performance analysis
- Track-by-track accuracy breakdown

## Recommendations

The script provides three types of recommendations:

1. **INCREASE_WEIGHT**: Variables higher in correct predictions
2. **DECREASE_WEIGHT**: Variables lower in correct predictions (high values hurt performance)
3. **REMOVE_OR_REVISE**: Variables with weak correlation to winning picks

Each recommendation includes:
- Priority level (HIGH, MEDIUM, LOW)
- Effect sizes
- Mean differences
- Specific actionable steps
