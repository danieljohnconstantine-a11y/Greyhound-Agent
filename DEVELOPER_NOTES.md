# Bet-Worthy Race Coloring Feature - Developer Notes

## Overview
This document explains the bet-worthy race detection and Excel color highlighting feature implemented for the Greyhound Analytics Pipeline.

## Feature Summary
The system now automatically identifies "bet-worthy" races based on configurable criteria and highlights them in the Excel output file (`todays_form_color.xlsx`) with a light yellow background color.

## Key Components

### 1. Bet-Worthy Detection (`src/bet_worthy.py`)
This module defines the logic for determining which races are worthy of betting attention.

**Default Criteria (any one condition triggers highlighting):**
- **Score Margin Percentage**: Top pick's margin ≥ 7% of top score
  - Formula: `(top_score - second_score) / top_score * 100`
  - Example: If top=50, second=45, margin=10%
- **Top Pick Confidence**: FinalScore ≥ 35
- **Absolute Score Margin**: Score difference ≥ 3.0 points

**Configurable Constants:**
```python
MIN_SCORE_MARGIN_PERCENT = 7.0      # Percentage margin threshold
MIN_TOP_PICK_CONFIDENCE = 35.0      # Minimum confidence score
MIN_SCORE_MARGIN_ABSOLUTE = 3.0     # Absolute point difference
```

**Key Functions:**
- `identify_bet_worthy_races(df)`: Identifies all bet-worthy races in dataset
- `is_race_bet_worthy(race_dogs_df)`: Checks if a single race meets criteria
- `print_bet_worthy_summary(bet_worthy_races)`: Displays analysis summary

### 2. Excel Formatting (`src/excel_formatter.py`)
Handles Excel export with conditional color highlighting using openpyxl.

**Features:**
- Applies light yellow background (`#FFFF99`) to bet-worthy races
- Leaves non-bet-worthy races with default white background
- Auto-adjusts column widths
- Freezes header row for easier scrolling
- Adds borders to all cells

**Configurable Constants:**
```python
BET_WORTHY_FILL_COLOR = "FFFF99"    # Light yellow
BET_WORTHY_FONT_COLOR = "000000"    # Black
HEADER_FILL_COLOR = "4472C4"        # Blue
HEADER_FONT_COLOR = "FFFFFF"        # White
```

**Key Functions:**
- `export_to_excel_with_formatting(df, bet_worthy_races, output_path)`: Main export function

### 3. Integration in `main.py`
The main pipeline now:
1. Processes PDF files as before
2. Calculates features and scores
3. **NEW:** Identifies bet-worthy races
4. **NEW:** Prints bet-worthy summary to console
5. **NEW:** Generates Excel file with color highlighting
6. Continues with other outputs (CSV files, picks, etc.)

## Usage

### Running the Pipeline
```bash
python main.py
```

The pipeline will:
- Process all PDFs in `data/` folder
- Generate `outputs/todays_form_color.xlsx` with highlighting
- Display bet-worthy races analysis in console

### Adjusting Thresholds

**To make more/fewer races bet-worthy:**

Edit `src/bet_worthy.py`:
```python
# More conservative (fewer highlighted races)
MIN_SCORE_MARGIN_PERCENT = 10.0
MIN_TOP_PICK_CONFIDENCE = 40.0
MIN_SCORE_MARGIN_ABSOLUTE = 5.0

# More aggressive (more highlighted races)
MIN_SCORE_MARGIN_PERCENT = 5.0
MIN_TOP_PICK_CONFIDENCE = 30.0
MIN_SCORE_MARGIN_ABSOLUTE = 2.0
```

### Customizing Colors

Edit `src/excel_formatter.py`:
```python
# Green highlighting
BET_WORTHY_FILL_COLOR = "90EE90"  # Light green

# Orange highlighting
BET_WORTHY_FILL_COLOR = "FFD580"  # Light orange

# Different header color
HEADER_FILL_COLOR = "28A745"  # Green
```

## Testing

### Quick Test with Existing Data
```python
import pandas as pd
from src.bet_worthy import identify_bet_worthy_races, print_bet_worthy_summary
from src.excel_formatter import export_to_excel_with_formatting

# Load data
df = pd.read_csv('outputs/todays_form.csv')

# Identify bet-worthy races
bet_worthy_races = identify_bet_worthy_races(df)
print_bet_worthy_summary(bet_worthy_races)

# Generate Excel
export_to_excel_with_formatting(df, bet_worthy_races, 'test_output.xlsx')
```

### Verifying Output
Open the Excel file and check:
- Bet-worthy races have light yellow highlighting
- Non-bet-worthy races have no highlighting
- Header row is blue with white text
- All cells have borders

## Performance Considerations

- Excel generation is slower than CSV (uses openpyxl)
- Processing 800+ rows takes ~1-2 seconds
- Memory usage is minimal (< 50 MB for typical datasets)

## Dependencies

Required packages:
```bash
pip install pandas openpyxl pdfplumber numpy
```

## Files Modified

1. **main.py** - Added bet-worthy detection and Excel export
2. **README.md** - Documented new feature and usage
3. **.gitignore** - Added to exclude cache files

## Files Added

1. **src/bet_worthy.py** - Bet-worthy detection logic
2. **src/excel_formatter.py** - Excel export with formatting
3. **DEVELOPER_NOTES.md** - This file

## Future Enhancements

Potential improvements:
- Add multiple highlight tiers (green for very confident, yellow for somewhat confident)
- Support custom color schemes from config file
- Add graphical visualization of score distributions
- Export bet-worthy races to separate sheet
- Add historical performance tracking for threshold optimization

## Troubleshooting

### Excel file has no highlighting
- Check that `bet_worthy_races` dict is populated
- Verify `FinalScore` column exists in DataFrame
- Ensure `Track` and `RaceNumber` columns match between data and bet_worthy dict

### Import errors
- Run `pip install pandas openpyxl pdfplumber numpy`
- Verify Python version >= 3.8

### Unexpected highlighting behavior
- Check threshold values in `src/bet_worthy.py`
- Review console output from `print_bet_worthy_summary()`
- Verify score calculation in `src/features.py`

## Contact

For questions or issues with this feature, refer to:
- README.md for user documentation
- src/bet_worthy.py for threshold configuration
- src/excel_formatter.py for color configuration
