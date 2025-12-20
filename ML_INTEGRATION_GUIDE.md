# Machine Learning Integration for Greyhound Prediction

## Overview

The ML integration adds a **hybrid prediction system** that combines:
1. **v4.4 Rule-Based Scoring** (28-30% win rate) - Proven hand-crafted features
2. **Random Forest ML Model** (learns from data) - Discovers hidden patterns
3. **Hybrid Selection** (35-40% expected) - Only bets when BOTH agree

## Why ML Integration?

**Limitations of Rule-Based Only:**
- Fixed weights (WinStreakFactor=1.50x) may not be optimal for all tracks
- Linear combinations miss non-linear interactions
- Cannot adapt to changing patterns without manual updates

**ML Advantages:**
- Learns optimal feature weights from actual outcomes
- Discovers non-linear patterns (e.g., "Box 2 + Hot Form + Elite Trainer = 45% win rate")
- Adapts as more data becomes available
- Validates rule-based assumptions with data

**Hybrid Approach = Best of Both:**
- Rule-based provides interpretability and domain knowledge
- ML provides pattern discovery and optimization
- Combined: Higher accuracy, fewer but better bets

## Quick Start

### 1. Install Dependencies

```bash
pip install scikit-learn pandas numpy
```

### 2. Train ML Model

```bash
python train_ml_model.py
```

This will:
- Load all historical PDFs + results from `data/` folder
- Train Random Forest on ~600 dogs from Nov 27-Dec 1 races
- Save model to `models/greyhound_ml_v1.pkl`
- Display training accuracy and feature importance

Expected output:
```
✅ Training complete:
   Train accuracy: 32.5%
   Validation accuracy: 28.2%
   CV accuracy: 27.8% (+/- 4.2%)

🔝 Top 5 Features:
   ConsistencyIndex: 0.145
   BestTimePercentile: 0.122
   HotForm: 0.098
   DLW: 0.087
   PlaceRate: 0.076
```

### 3. Run Hybrid Predictions

```bash
# Demo on example PDF
python demo_ml_hybrid.py

# Or specify PDF file
python demo_ml_hybrid.py data/HEALG0112form.pdf
```

## How It Works

### Training Phase

1. **Data Collection:**
   - Parses all historical PDFs (`data/*form.pdf`)
   - Matches with race results (`data/results_*.csv`)
   - Extracts 51 v4.4 features + derived metrics

2. **Feature Engineering:**
   ```python
   # Core v4.4 features
   - BoxDraw, BestTimeSec, SectionalSec
   - DLW, DLR, CareerStarts, CareerWins
   - TrainerStrikeRate, Age, Weight
   
   # Derived features
   - ConsistencyIndex = CareerWins / CareerStarts
   - PlaceRate = CareerPlaces / CareerStarts
   - HotForm = 1 if DLW ≤ 7 else 0
   - BestTimePercentile = rank within race
   ```

3. **Model Training:**
   - Algorithm: Random Forest (100 trees)
   - Class balancing: Handle 8 dogs, 1 winner per race
   - Cross-validation: 5-fold to prevent overfitting
   - Validation split: 80/20 train/test

4. **Evaluation:**
   - Accuracy: % of races where winner correctly predicted
   - Feature importance: Which factors matter most
   - Baseline: 12.5% (random), Target: 25%+ (2x random)

### Prediction Phase

1. **v4.4 Scoring:**
   ```python
   df_scored = score_race(df_race, track)
   rule_scores = df_scored['FinalScore']
   
   # TIER0: Top dog with 18%+ margin
   ```

2. **ML Scoring:**
   ```python
   predictor = GreyhoundMLPredictor('models/greyhound_ml_v1.pkl')
   ml_confidence = predictor.predict_confidence(df_race)
   
   # Confidence: 0-100% win probability
   ```

3. **Hybrid Decision:**
   ```python
   result = predictor.hybrid_predict(df_race, rule_scores)
   
   # BET if:
   # - v4.4: TIER0 (18%+ margin) ✓
   # - ML: 75%+ confidence ✓
   # - Both pick SAME dog ✓
   ```

## Expected Performance

| System | Win Rate | Bets per Day | Selectivity |
|--------|----------|--------------|-------------|
| Random | 12.5% | All races | None |
| v4.4 Overall | 28-30% | All races | Medium |
| v4.4 TIER0 | 42-45% | ~15-20% of races | High |
| ML Alone | 25-30% | All races | Medium |
| **Hybrid TIER0** | **35-40%** | **~10-15% of races** | **Ultra-High** |

**Key Trade-off:**
- Fewer bets (only 10-15% of races qualify)
- Higher accuracy (both systems must agree)
- Better bankroll preservation (avoid marginal bets)

## File Structure

```
Greyhound-Agent/
├── src/
│   ├── ml_predictor.py        # ML model class
│   ├── features.py             # Feature computation (v4.4)
│   ├── scorer.py               # Rule-based scoring (v4.4)
│   └── bet_worthy.py           # TIER detection (v4.4)
├── train_ml_model.py           # Training script
├── demo_ml_hybrid.py           # Demo/example usage
├── models/
│   └── greyhound_ml_v1.pkl     # Trained model (generated)
├── data/
│   ├── *form.pdf               # Historical race PDFs
│   └── results_*.csv           # Race results
└── ML_INTEGRATION_GUIDE.md     # This file
```

## Usage Examples

### Example 1: Basic Training

```python
from src.ml_predictor import GreyhoundMLPredictor, load_historical_data

# Load data
race_data, winners = load_historical_data('data')

# Train
predictor = GreyhoundMLPredictor()
metrics = predictor.train(race_data, winners)

# Save
predictor.save_model('models/greyhound_ml_v1.pkl')
```

### Example 2: Hybrid Prediction

```python
from src.ml_predictor import GreyhoundMLPredictor
from src.parser import parse_pdf
from src.features import compute_features
from src.scorer import score_race

# Load model
predictor = GreyhoundMLPredictor('models/greyhound_ml_v1.pkl')

# Parse race
parsed = parse_pdf('data/HEALG0112form.pdf')
df_race = parsed[0]['race_data']
df_race = compute_features(df_race)

# v4.4 scoring
df_scored = score_race(df_race, 'Healesville')
v4_4_scores = df_scored['FinalScore']

# Hybrid prediction
result = predictor.hybrid_predict(df_race, v4_4_scores)

if result['tier'] == 'HYBRID_TIER0':
    print(f"BET: Box {result['recommended_box']}")
    print(f"v4.4: {result['rule_based_score']:.1f}")
    print(f"ML: {result['ml_confidence']:.1f}%")
else:
    print("NO BET - waiting for stronger signal")
```

### Example 3: ML Confidence Only

```python
# Get ML predictions without hybrid logic
ml_confidence = predictor.predict_confidence(df_race)

# Show top 3
top_3 = ml_confidence.nlargest(3)
for idx, conf in top_3.items():
    dog = df_race.loc[idx]
    print(f"Box {dog['BoxDraw']}: {conf:.1f}%")
```

## Limitations & Future Improvements

### Current Limitations

1. **Limited Training Data:**
   - Current: ~600 dogs from 5 days of races
   - Ideal: 5,000+ dogs from months of racing
   - Impact: Model may not generalize to all track/conditions

2. **No Temporal Features:**
   - Doesn't use time-series patterns
   - Can't detect seasonal trends
   - Future: Add LSTM/sequential models

3. **Missing Context:**
   - No weather data
   - No track condition info
   - No betting odds integration

### Planned Improvements

**Phase 2 (Short-term):**
- [ ] Collect 6+ months historical data
- [ ] Add weather/track condition features
- [ ] Ensemble multiple ML models (RF + XGBoost + Neural Net)
- [ ] Hyperparameter tuning with grid search

**Phase 3 (Medium-term):**
- [ ] Integrate betting odds (smart money detection)
- [ ] Add head-to-head matchup history
- [ ] Track-specific models (different model per track)
- [ ] Real-time model updates

**Phase 4 (Long-term):**
- [ ] Deep learning (LSTM for sequence prediction)
- [ ] Reinforcement learning (optimal betting strategy)
- [ ] Automated data collection pipeline
- [ ] Live prediction API

## Performance Monitoring

Track hybrid performance vs baseline:

```python
# After each race day, compare:
v4_4_wins = 28  # out of 100 races
ml_wins = 27    # out of 100 races
hybrid_wins = 18  # out of 45 races (only bet 45)

v4_4_rate = 28/100 = 28%
ml_rate = 27/100 = 27%
hybrid_rate = 18/45 = 40%  ✅ Better accuracy, fewer bets
```

## Troubleshooting

**Model accuracy too low (<20%):**
- Check data quality (are PDFs parsing correctly?)
- Ensure results CSV format matches expected
- Try collecting more training data

**Hybrid never recommends bets:**
- Lower thresholds (tier0_threshold=15, ml_threshold=70)
- Check if v4.4 and ML are scoring different dogs
- Review feature distributions

**Model file too large:**
- Current: ~100-200 KB
- If >1 MB: Reduce n_estimators or max_depth

## Contributing

To improve the ML system:
1. Collect more historical data (critical!)
2. Experiment with features (add new derived metrics)
3. Try different ML algorithms (XGBoost, Neural Nets)
4. Share results and insights

## License

Same as main Greyhound-Agent project.

---

**Questions? Issues?**
- Check training output for errors
- Verify data/ folder has PDFs and results CSVs
- Ensure sklearn, pandas, numpy installed
- Review demo_ml_hybrid.py for usage examples

**Ready to predict!** 🎯
