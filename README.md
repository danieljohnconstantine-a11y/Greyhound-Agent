# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms with ultra-selective betting strategy.

## Features
- PDF-to-text ingestion with enhanced timing data extraction
- Advanced race form parsing
- Trainer matching and career statistics
- Multi-factor feature scoring (28+ features)
- Ultra-selective betting strategy (35-40% win rates on bet-worthy races)
- Color-coded Excel exports with conditional formatting
- Optional ML predictions for enhanced confidence
- Top pick selection with tier-based confidence levels

## Installation
```bash
pip install -r requirements.txt
```

## Usage

### Daily Predictions (Today's Races)
1. Place today's race form PDFs in the `data_predictions/` folder
2. Run `run_predictions_today.bat` (Windows) or `python main.py data_predictions/*.pdf`
3. Check results in `outputs/`:
   - `todays_form.xlsx` - Color-coded picks with bet-worthy races highlighted
   - `todays_form.csv` - Raw data
   - `ranked.csv` - All dogs ranked by score
   - `picks.csv` - Top picks per race

### Historical Analysis
1. Place PDF form files in the `data/` folder
2. Run `main.py` (or use `run_main.bat` on Windows)
3. Check results in `outputs/`

### ML Training (Optional)
1. Ensure you have historical race data in `data/` folder
2. Run `train_ml.bat` (Windows) or `python train_ml_model.py`
3. The trained model will be used automatically in future predictions

## Output Files
- `todays_form.xlsx`: Color-coded Excel with bet-worthy races highlighted
- `todays_form.csv`: Parsed race data
- `ranked.csv`: All dogs ranked by FinalScore
- `picks.csv`: Top betting picks

## Bet-Worthy Strategy

The system uses an **ultra-selective** betting approach with 4 tiers:

- **TIER 0 (LOCK)**: 35-40% win rate - Perfect alignment of all factors
- **TIER 1 (Premium)**: 28-32% win rate - Strong signals across multiple factors
- **TIER 2 (High)**: 22-28% win rate - Good confidence on key indicators
- **TIER 3 (Standard)**: 18-22% win rate - Baseline confidence
- **NO BET**: Skip races with insufficient confidence

Only bet-worthy races are highlighted in the Excel output.

## Project Structure
```
├── main.py                  # Main pipeline with bet-worthy logic
├── train_ml_model.py        # ML model training script
├── src/                     # Core source code
│   ├── parser.py            # Enhanced PDF parsing with timing data
│   ├── features.py          # Advanced 28+ feature scoring
│   ├── bet_worthy.py        # Ultra-selective betting strategy
│   ├── excel_export.py      # Color-coded Excel generation
│   ├── excel_formatter.py   # Excel formatting with highlighting
│   └── ml_predictor.py      # ML predictions (optional)
├── tests/                   # Test files
├── data/                    # Historical race PDFs + results
├── data_predictions/        # Today's race PDFs (for daily predictions)
├── models/                  # Trained ML models
├── outputs/                 # Generated results (CSV + Excel)
└── legacy/                  # Legacy/unused code (preserved for reference)
```
