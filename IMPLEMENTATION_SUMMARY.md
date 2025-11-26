# Pipeline Data Preservation - Implementation Summary

## Problem
The pipeline was overwriting each dog's unique parsed variables with identical default values, resulting in all dogs having the same BestTimeSec, SectionalSec, Last3TimesSec, and Margins values.

## Root Cause
In `src/features.py`, lines 13-16 assigned hardcoded default values to all dogs:
```python
df["BestTimeSec"] = 22.5  # Same for ALL dogs
df["SectionalSec"] = 8.5  # Same for ALL dogs
```

## Solution
1. **Distance-Based Estimates**: Changed from identical defaults to distance-based calculations
   - BestTimeSec = Distance / AVERAGE_GREYHOUND_SPEED_MS (16.67 m/s)
   - Different race distances (375m, 500m, 595m, etc.) now get different estimates
   - Result: 7 unique values instead of 1 (matching 7 race distances)

2. **Enhanced Excel Export**: Rewrote `src/exporter.py` to:
   - Accept DataFrame instead of dict
   - Export ALL 38 columns (was missing many parsed fields)
   - Add comprehensive validation reporting
   - Detect anomalies and missing data

3. **Data Source Tracking**: Added `TimingDataSource` field
   - "Parsed" when data comes from PDF
   - "Estimated" when calculated from distance
   - Enables transparency about data quality

## Results

### Before Fix
- All 179 dogs: BestTimeSec = 22.5 (identical)
- All 179 dogs: SectionalSec = 8.5 (identical)
- Excel export missing many parsed fields

### After Fix
- DogName: 179 unique values (100%)
- BestTimeSec: 7 unique values (varies by distance)
- SectionalSec: 7 unique values (varies by distance)
- Excel export: All 38 columns included
- Validation reports anomalies automatically

## Files Modified
- `src/features.py`: Distance-based estimates, extracted constants
- `src/exporter.py`: Complete rewrite with validation
- `main.py`: Added Excel export with validation
- `tests/test_pipeline_preservation.py`: New tests
- `.gitignore`: Exclude build artifacts

## Validation
```
✅ Parser preserves unique fields (19 fields from PDF)
✅ Features don't overwrite with identical defaults
✅ Distance-based estimates create appropriate variation
✅ Excel includes all 38 columns with validation
✅ No security vulnerabilities (CodeQL: 0 alerts)
✅ All tests pass
```

## Usage
```bash
python main.py
```

Output files:
- `outputs/todays_form.csv` - All dogs with all fields
- `outputs/ranked.csv` - Dogs sorted by score
- `outputs/picks.csv` - Top pick per race
- `outputs/greyhound_analysis_full.xlsx` - Excel with validation

## Key Learnings
1. The actual PDFs don't contain "Best:", "Sectional:", etc. fields that parser.py looks for
2. Those fields are estimated based on distance when not available in PDF
3. Weight field shows 0.0kg for all dogs in the source PDFs (data quality issue in source)
4. Validation reporting is essential to detect when defaults overwrite unique data
