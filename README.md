# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection

## Usage
1. Place your PDF form files in the `data/` folder.
2. Run `main.py` (or use `run_main.bat` on Windows)
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data
- `ranked.csv`: Scored dogs
- `picks.csv`: Top betting picks

## Project Structure
```
├── main.py              # Main pipeline orchestration
├── src/                 # Core source code
│   ├── parser.py        # PDF parsing logic
│   └── features.py      # Feature computation & scoring
├── tests/               # Test files
├── data/                # Input PDF files
├── outputs/             # Generated CSV results
└── legacy/              # Legacy/unused code (preserved for reference)
```
