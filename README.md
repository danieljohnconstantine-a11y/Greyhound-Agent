# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms with intelligent bet-worthy race highlighting.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection
- **Bet-worthy race detection and color highlighting**
- **Speed matrix analysis and optimization**
- **Prediction accuracy tracking**

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a step-by-step guide to running the pipeline.

## Usage
1. Place your `.pdf` form file in the `data/` folder.
2. Run `main.py`
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data (CSV format)
- `todays_form_color.xlsx`: **Parsed race data with color highlighting for bet-worthy races (Excel format)**
- `ranked.csv`: Scored dogs
- `picks.csv`: Top 5 betting picks

## Advanced Features

### 1. Bet-Worthy Race Highlighting

The Excel output (`todays_form_color.xlsx`) includes color highlighting to identify races that meet "bet-worthy" criteria. Within each bet-worthy race, dogs are color-coded by their predicted position based on FinalScore:

- **🟢 Green (Light Green)**: 1st place - Top pick (highest FinalScore)
- **🟠 Orange (Light Orange)**: 2nd place - Second pick
- **🔴 Red (Light Pink)**: 3rd place - Third pick
- **🟡 Yellow (Light Yellow)**: Other dogs in bet-worthy races

Non-bet-worthy races remain **white** (no highlighting).

#### What Makes a Race "Bet-Worthy"?

A race is considered bet-worthy if **any** of the following conditions are met:

1. **Score Margin Percentage**: The top pick's score margin vs. the next highest is ≥ 7% (configurable)
2. **Top Pick Confidence**: The model confidence (FinalScore) for the top pick is ≥ 35 (configurable)
3. **Absolute Score Margin**: The absolute score difference between top and second pick is ≥ 3.0 (configurable)

See [DEVELOPER_NOTES.md](DEVELOPER_NOTES.md) for threshold tuning details.

### 2. Speed Matrix Analysis

Optimize scoring weights based on actual race results. See [SPEED_MATRIX_USER_GUIDE.md](SPEED_MATRIX_USER_GUIDE.md) for details.

```bash
python analyze_speed_matrix.py
```

### 3. Prediction Accuracy Analysis

Track and analyze prediction accuracy against actual results. See [ANALYSIS_README.md](ANALYSIS_README.md) for details.

```bash
python analyze_predictions.py
```

## Dependencies

- pandas
- numpy
- pdfplumber
- openpyxl
- scikit-learn (for advanced analysis)
- scipy (for statistical analysis)

Install with: `pip install pandas numpy pdfplumber openpyxl scikit-learn scipy`
