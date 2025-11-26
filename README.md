# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms with intelligent bet-worthy race highlighting.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection
- **Bet-worthy race detection and color highlighting**

## Usage
1. Place your `.pdf` form file in the `data/` folder.
2. Run `main.py`
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data (CSV format)
- `todays_form_color.xlsx`: **Parsed race data with color highlighting for bet-worthy races (Excel format)**
- `ranked.csv`: Scored dogs
- `picks.csv`: Top 5 betting picks

## Bet-Worthy Race Highlighting

The Excel output (`todays_form_color.xlsx`) includes color highlighting to identify races that meet "bet-worthy" criteria. Within each bet-worthy race, dogs are color-coded by their predicted position based on FinalScore:

- **🟢 Green (Light Green)**: 1st place - Top pick (highest FinalScore)
- **🟠 Orange (Light Orange)**: 2nd place - Second pick
- **🔴 Red (Light Pink)**: 3rd place - Third pick
- **🟡 Yellow (Light Yellow)**: Other dogs in bet-worthy races

Non-bet-worthy races remain **white** (no highlighting).

### What Makes a Race "Bet-Worthy"?

A race is considered bet-worthy if **any** of the following conditions are met:

1. **Score Margin Percentage**: The top pick's score margin vs. the next highest is ≥ 7% (configurable)
   - Calculated as: `(top_score - second_score) / top_score * 100`
   - Example: Top score 50, second score 45 → margin is 10%
2. **Top Pick Confidence**: The model confidence (FinalScore) for the top pick is ≥ 35 (configurable)
3. **Absolute Score Margin**: The absolute score difference between top and second pick is ≥ 3.0 (configurable)

### Adjusting Thresholds

You can tune the bet-worthy detection by modifying the constants in `src/bet_worthy.py`:

```python
# Minimum score margin percentage (default: 7.0%)
MIN_SCORE_MARGIN_PERCENT = 7.0

# Minimum confidence for top pick (default: 35.0)
MIN_TOP_PICK_CONFIDENCE = 35.0

# Minimum absolute score difference (default: 3.0, set to None to disable)
MIN_SCORE_MARGIN_ABSOLUTE = 3.0
```

**Tips for tuning:**
- **Increase thresholds** to be more conservative (fewer highlighted races, higher confidence)
- **Decrease thresholds** to be more aggressive (more highlighted races, lower confidence)
- **Monitor results** and adjust based on betting performance

### Color Customization

You can customize the highlight colors in `src/excel_formatter.py`:

```python
# Position-based colors for bet-worthy races
FIRST_PLACE_COLOR = "90EE90"   # Light green (top pick)
SECOND_PLACE_COLOR = "FFD580"  # Light orange (second pick)
THIRD_PLACE_COLOR = "FFB6C1"   # Light red/pink (third pick)
OTHER_BET_WORTHY_COLOR = "FFFF99"  # Light yellow (other dogs)
```

## Dependencies

- pandas
- numpy
- pdfplumber
- openpyxl

Install with: `pip install pandas numpy pdfplumber openpyxl`
