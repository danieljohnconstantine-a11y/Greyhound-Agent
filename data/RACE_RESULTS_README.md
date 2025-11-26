# Race Results Data

This directory contains actual race results used for validating and optimizing predictions.

## Files

### race_results_nov_2025.csv
Race results from September-November 2025 across multiple Australian tracks.

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
- **September 2025:**
  - Sale (Sep 7) - 12 races ✓ MATCHES SALE_2025-09-07.pdf
  - Darwin (Sep 7) - 8 races ✓ MATCHES DRWN_2025-09-07.pdf
  - Q Straight (Sep 7) - 12 races ✓ MATCHES QSTR_2025-09-07.pdf
- **October 2025:**
  - Angle Park (Oct 16) - 12 races ✓ MATCHES ANGLG1610form.pdf
  - Bendigo (Oct 16) - 11 races ✓ MATCHES BDGOG1610form.pdf
- **November 2025:**
  - Horsham (Nov 18) - 12 races
  - Warragul (Nov 18) - 12 races
  - Angle Park (Nov 18, 22) - 20 races
  - Launceston (Nov 18) - 10 races
  - Bendigo (Nov 22) - 10 races
  - Sandown Park (Nov 22) - 12 races
  - Cannington (Nov 22) - 11 races
  - Q Lakeside (Nov 22) - 10 races
  - Sandown (Nov 22) - 12 races
  - Dubbo (Nov 22) - 12 races ✓ MATCHES DUBBG2211form.pdf
  - Wentworth Park (Nov 22) - 10 races ✓ MATCHES WENPG2211form.pdf
  - Healesville (Nov 23) - 12 races
  - Sale (Nov 23) - 12 races
  - **Richmond (Nov 23) - 11 races** ✨ NEW
  - **Grafton (Nov 23) - 11 races** ✨ NEW
  - **Broken Hill (Nov 23) - 9 races** ✨ NEW
  - **Mount Gambier (Nov 23) - 11 races** ✨ NEW
  - **BetDeluxe Capalaba (Nov 23) - 11 races** ✨ NEW
  - **BetDeluxe Rockhampton (Nov 23) - 12 races** ✨ NEW
  - **Gawler (Nov 23) - 9 races** ✨ NEW
  - **Q2 Parklands (Nov 23) - 12 races** ✨ NEW

**Total:** 320 races across 24 tracks (expanded from 210 races)

## PDF Coverage

All PDF form guides in the repository now have matching race results:

**September 2025:**
- ✅ SALE_2025-09-07.pdf - Sale Sep 7
- ✅ DRWN_2025-09-07.pdf - Darwin Sep 7
- ✅ QSTR_2025-09-07.pdf - Q Straight Sep 7

**October 2025:**
- ✅ ANGLG1610form.pdf - Angle Park Oct 16
- ✅ BDGOG1610form.pdf - Bendigo Oct 16
- ⏭️ BRHG1910form.pdf - Bathurst Oct 19 (skipped per user request)

**November 22, 2025:**
- ✅ DUBBG2211form.pdf - Dubbo Nov 22
- ✅ WENPG2211form.pdf - Wentworth Park Nov 22

**November 23, 2025:**
- ✅ RICHG2311form.pdf - Richmond Nov 23
- ✅ GRAFG2311form.pdf - Grafton Nov 23
- ✅ BRHG2311form.pdf - Broken Hill Nov 23
- ✅ HEALG2311form.pdf - Healesville Nov 23
- ✅ MTGG2311form.pdf - Mount Gambier Nov 23
- ✅ CAPAG2311form.pdf - BetDeluxe Capalaba Nov 23
- ✅ SALEG2311form.pdf - Sale Nov 23
- ✅ ROCKG2311form.pdf - BetDeluxe Rockhampton Nov 23
- ✅ GAWLG2311form.pdf - Gawler Nov 23
- ✅ QPRKG2311form.pdf - Q2 Parklands Nov 23
- ✅ DRWNG2311form.pdf - Darwin Nov 23

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
- Date range: September 7 - November 23, 2025
- Various tracks across NSW, SA, VIC, WA, QLD, TAS, NT
