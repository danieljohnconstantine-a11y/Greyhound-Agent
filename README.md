# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection
- **NEW**: Prediction accuracy analysis

## Usage
1. Place your `.txt` form file in the `data/` folder.
2. Run `main.py`
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data
- `ranked.csv`: Scored dogs
- `picks.csv`: Top 5 betting picks
- `todays_form_color.xlsx`: Full analysis with color coding

## Prediction Accuracy Analysis

After races are complete, you can analyze how well the predictions performed:

```bash
python analyze_predictions.py actual_winners.txt
```

See `ANALYSIS_README.md` for detailed instructions on the accuracy analysis tool.
