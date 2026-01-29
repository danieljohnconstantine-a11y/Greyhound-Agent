# 🎯 Greyhound-Agent Project Goal

## What Is This Project?

**Greyhound-Agent** is an **AI-powered greyhound racing prediction system** designed to help bettors make data-driven decisions and improve their win rates at Australian greyhound tracks.

---

## 🎪 The Core Goal

**To predict which greyhound will win a race with accuracy significantly better than random chance, using machine learning and comprehensive data analysis.**

Instead of relying on gut feelings, tipsters, or manual form analysis, this system:
1. Extracts data from official race form PDFs
2. Analyzes 76+ features per dog (speed, form, consistency, track history, etc.)
3. Uses machine learning models trained on 6,000+ historical races
4. Generates probability-based predictions for each dog
5. Identifies the most likely winners

---

## 👥 Who Is This For?

**Target Users:**
- 🎲 **Greyhound racing bettors** who want better predictions
- 📊 **Data-driven punters** who prefer analytics over hunches
- 💰 **Serious gamblers** looking to improve ROI
- 🏆 **Professional bettors** who need systematic edge

---

## 🔑 Key Capabilities

### 1. Automated Data Processing
- Parses official race form PDFs from Australian tracks
- Extracts dog names, times, boxes, trainer info, past performance
- Handles 30+ different track formats automatically

### 2. Comprehensive Feature Analysis
- **76+ features per dog** including:
  - Career statistics (wins, places, starts)
  - Performance metrics (best time, sectionals, speed ratings)
  - Recent form (last 5 races, trends, momentum)
  - Track-specific data (track win rate, box performance)
  - Advanced metrics (consistency, reliability, potential)

### 3. Machine Learning Predictions
- **Three-model ensemble**: Random Forest + Gradient Boosting + XGBoost
- **Track-specific models**: Separate training for each track's unique characteristics
- **Probability outputs**: Shows confidence level for each prediction (e.g., 18.7% vs 11.0%)

### 4. Daily Prediction Workflow
- Drop today's PDFs in `data_predictions/` folder
- Run prediction script
- Get Excel output with ranked picks
- Place bets on top selections

---

## 📈 Expected Performance

**Realistic Goals:**
- **Top-1 Accuracy**: 20-25% (vs 12.5% random for 8-dog race)
- **Top-3 Accuracy**: 50-60% (vs 37.5% random)
- **ROI**: Positive returns over multiple weeks
- **Win Rate**: 25%+ on top picks

**Current Status:**
- ⚠️ System has issues with identical scores (being investigated)
- ⚠️ Some features not available in PDFs (limiting differentiation)
- 🔧 Improvements needed for production betting

---

## 🔄 How It Works (High-Level)

```
1. INPUT: Race form PDFs
   ↓
2. PARSING: Extract dog data, times, statistics
   ↓
3. FEATURES: Calculate 76+ features per dog
   ↓
4. SCALING: Normalize features using historical data
   ↓
5. MODELS: Run through RF, GB, XGBoost
   ↓
6. ENSEMBLE: Average three model predictions
   ↓
7. OUTPUT: Ranked list with probability scores
```

---

## 💡 The Value Proposition

**Instead of:**
- ❌ Reading 50-page form guides manually
- ❌ Relying on paid tipster services ($$$)
- ❌ Making emotional or biased selections
- ❌ Missing subtle patterns in data

**You get:**
- ✅ Automated, consistent analysis
- ✅ Data-driven, unbiased predictions
- ✅ Track-specific learning from 6,000+ races
- ✅ Probability-based confidence levels
- ✅ Fast daily predictions (5 minutes)

---

## 🎯 Success Metrics

The project is successful when:
1. **Predictions beat random chance** by 50%+ (e.g., 18% vs 12.5%)
2. **Top-3 accuracy** reaches 50%+
3. **Users achieve positive ROI** over multiple weeks
4. **Clear differentiation** between dogs (no identical scores)
5. **Consistent performance** across different tracks

---

## 🚧 Current Challenges

### Issues Identified:
1. **Identical scores problem**: 5 dogs getting same prediction
2. **Limited feature variance**: Only 10-15 features varying from PDFs
3. **Missing career data**: 60+ features defaulting to zero
4. **Model over-reliance**: Trained on features not available at prediction time

### Being Fixed:
- Investigation completed (see SCORING_INVESTIGATION_DETAILED.md)
- Solutions proposed (rule-based backup, retrain with limited features)
- Timeline: 1-2 weeks for proper fixes

---

## 📊 Project Status

**Current State**: 
- ✅ Data pipeline working
- ✅ PDF parsing functional
- ✅ ML models trained
- ✅ Prediction script operational
- ⚠️ Score differentiation needs improvement
- ⚠️ Feature engineering needs refinement

**Next Steps:**
1. Fix identical scores issue
2. Implement rule-based backup scoring
3. Retrain with only available features
4. Validate on historical results
5. Test with real money (small stakes)

---

## 🎲 Bottom Line

**This project aims to give greyhound racing bettors a scientific, data-driven edge through machine learning predictions - turning form analysis from an art into a science.**

**Current status**: System works but needs refinement before reliable betting.

**Expected outcome**: 20-25% win rate (vs 12.5% random), positive ROI, consistent performance.

**Time to production**: 2-4 weeks with current fixes being implemented.

---

## 📚 Key Documents

- **README.md**: Installation and usage instructions
- **QUICK_START_GUIDE.md**: Daily workflow reference
- **SCORING_INVESTIGATION_DETAILED.md**: Current issues analysis
- **COMPREHENSIVE_MODEL_EVALUATION.md**: Model performance details
- **train_ml_track_ensemble.py**: ML training code
- **ml_predictor.py**: Daily prediction script

---

**Last Updated**: January 29, 2026  
**Version**: Beta - Under Active Development  
**License**: Private/Personal Use
