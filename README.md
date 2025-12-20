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

## Usage

### Daily Predictions (Today's Races)
1. Place today's race form PDFs in the `data_predictions/` folder
2. Run `run_predictions_today.bat` (Windows) or `python main.py data_predictions/*.pdf`
3. Check results in `outputs/`

### Historical Analysis
1. Place PDF form files in the `data/` folder
2. Run `main.py` (or use `run_main.bat` on Windows)
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data
- `ranked.csv`: Scored dogs
- `picks.csv`: Top betting picks

## Project Structure
```
├── main.py                  # Main pipeline orchestration
├── src/                     # Core source code
│   ├── parser.py            # PDF parsing logic
│   └── features.py          # Feature computation & scoring
├── tests/                   # Test files
├── data/                    # Historical race PDFs
├── data_predictions/        # Today's race PDFs (for daily predictions)
├── outputs/                 # Generated CSV results
└── legacy/                  # Legacy/unused code (preserved for reference)
```
