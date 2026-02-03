# QUICK START GUIDE

## 🚀 3-Minute Quick Reference

### First Time Setup (One-Time, 30-60 min)

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
source venv/bin/activate
python train_ml_track_ensemble.py
```

Wait for completion. Models saved to `models/` directory.

---

### Daily Predictions (5 minutes)

**1. Add Yesterday's Results:**
```bash
nano data/results_YYYY-MM-DD.csv
```

Format:
```
Track,Race,Position1,Position2,Position3,Position4
Angle Park,1,3,5,1,7
```

**2. Move Old PDFs:**
```bash
mv data_predictions/*YESTERDAY* data/
```

**3. Download Today's Race Forms:**
- Save to: `data_predictions/`

**4. Generate Predictions:**
```bash
python ml_predictor.py
```

**5. Review Results:**
```bash
explorer.exe outputs/track_ensemble_predictions.xlsx
```

---

### Key Commands

| Task | Command |
|------|---------|
| Train models | `python train_ml_track_ensemble.py` |
| Make predictions | `python ml_predictor.py` |
| Check accuracy | `python analyze_accuracy.py` |
| Validate data | `python validate_data_pipeline.py` |

---

### What to Look For

**Good Predictions:**
- ✅ Score range: 11-18 points
- ✅ Variance: >2.0 std dev
- ✅ Top picks: >17.0 score

**Warning Signs:**
- ⚠️ All dogs same score (maiden race)
- ⚠️ Missing tracks (need more data)
- ⚠️ Parsing errors (PDF format changed)

---

### Files to Track

| File | Purpose |
|------|---------|
| `outputs/track_ensemble_predictions.xlsx` | Main predictions |
| `outputs/track_ensemble_summary.txt` | Performance stats |
| `logs/predictions_*.log` | Execution logs |
| `prediction_tracking.csv` | Accuracy tracking |

---

### Success Metrics

- Win Rate: >25%
- Place Rate: >70%
- ROI: Positive over 2+ weeks

---

### Getting Help

See `DETAILED_STEPS_TO_PROCEED.md` for comprehensive guide.
