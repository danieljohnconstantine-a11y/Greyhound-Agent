# Race Results Data

This directory contains actual race results used for validating and optimizing predictions.

## Files

### race_results_nov_2025.csv
Race results from November 18-23, 2025 across multiple Australian tracks.

**Format:**
- `Track`: Track name (e.g., Bendigo, Sandown Park, Angle Park)
- `RaceDate`: Date of race (YYYY-MM-DD format)
- `RaceNumber`: Race number (1-12)
- `WinnerBox`: Box number of winning dog
- `SecondBox`: Box number of second place (when available)
- `ThirdBox`: Box number of third place (when available)
- `FourthBox`: Box number of fourth place (when available)
- `Distance`: Race distance in meters (e.g., 342m, 515m)
- `WinnerName`: Name of winning dog
- `WinnerTime`: Winning time in seconds

**Tracks Included:**
- Horsham (Nov 18) - 12 races
- Warragul (Nov 18) - 12 races
- Angle Park (Nov 18, 22) - 20 races
- Launceston (Nov 18) - 10 races
- Bendigo (Nov 22) - 10 races
- Sandown Park (Nov 22) - 12 races
- Cannington (Nov 22) - 11 races
- Q Lakeside (Nov 22) - 10 races
- Sandown (Nov 22) - 12 races
- Healesville (Nov 23) - 12 races
- Sale (Nov 23) - 12 races

**Total:** 133 races across 11 tracks

## Usage

Use this data with the results analyzer tool:

```bash
python -m src.results_analyzer --results data/race_results_nov_2025.csv --predictions outputs/todays_form.csv
```

The analyzer will:
1. Match predictions with actual results
2. Calculate accuracy metrics (winner hit rate, top-3 hit rate)
3. Identify which features correlate with winning
4. Optimize scoring weights using machine learning
5. Generate confidence scores for predictions

## Data Sources

Race results collected from:
- Official Australian greyhound racing results
- Multiple dates: November 18, 22, 23, 2025
- Various tracks across SA, VIC, WA, QLD, TAS
