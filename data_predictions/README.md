# Daily Predictions Folder

## Purpose
This folder is for **today's race form PDFs** that you want to get predictions for BEFORE the races run.

## Usage

### Daily Workflow:
1. **Download today's race form PDFs** from your greyhound racing website
2. **Copy PDFs here** (e.g., `BDGOG0612form.pdf`, `MAITG0612form.pdf`)
3. **Run predictions** using one of these methods:

**Windows:**
```cmd
python main.py data_predictions\*.pdf
```

**Linux/Mac:**
```bash
python main.py data_predictions/*.pdf
```

### After Races Run:
1. **Get results** - Download results CSV for the day
2. **Move PDFs to data/** - Move race form PDFs from `data_predictions/` to `data/`
3. **Add results to data/** - Place results CSV in `data/` folder
4. **Retrain ML model** - Run `train_ml.bat` to update the ML model with new data

## Folder Structure

```
data_predictions/     ← Today's races (for predictions)
data/                 ← Historical races + results (for ML training)
models/               ← Trained ML models
```

## Why Separate Folders?

- **data_predictions/** - Clean folder with ONLY today's races to predict
- **data/** - All historical race PDFs + results CSVs for ML training
- Prevents accidentally re-analyzing hundreds of old races
- Keeps prediction runs fast and focused

## Example

**Before races (6am):**
```
data_predictions/
  BDGOG0612form.pdf
  MAITG0612form.pdf
  HEALG0612form.pdf
```
Run: `python main.py data_predictions\*.pdf` → Get predictions

**After races (6pm):**
```
Move PDFs to: data/
Add results: data/results_2025-12-06.csv
Run: train_ml.bat → Update ML model
```

**Next day:**
```
Delete old PDFs from data_predictions/
Add new PDFs to data_predictions/
Repeat cycle
```
