# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies
- pandas - Data manipulation
- pdfplumber - PDF text extraction
- openpyxl - Excel file export
- numpy - Numerical computations

## Usage
1. Place your `.pdf` form files in the `data/` folder.
2. Run `python main.py`
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data (all fields)
- `ranked.csv`: Scored dogs sorted by performance
- `picks.csv`: Top 5 betting picks
- `greyhound_analysis_full.xlsx`: Complete Excel export with validation
