# FACTORS NOT WORKING ANALYSIS

## Executive Summary

**User's Question**: Which factors are still not working for each dog?

**Answer**: 
- **40-45 factors** are NOT working (missing/zero/default)
- **20-25 factors** are PARTIALLY working (limited variance)
- **5-10 factors** are WORKING well (clear differentiation)

**Impact**: Limited score differentiation, heavy reliance on speed times

---

## Part 1: Complete Factor Audit (76 Features)

### 🔴 NOT WORKING (40-45 Factors)

#### Career Statistics (4 factors) - ALL MISSING
1. **CareerWins** → 0 (defaults to zero, not in PDF)
2. **CareerPlaces** → 0 (defaults to zero, not in PDF)
3. **PrizeMoney** → 0 (defaults to zero, not in PDF)
4. **CareerEarnings** → 0 (derived from PrizeMoney)

**Why Not Working**: PDFs don't include career stats in parsed fields  
**Impact**: Can't calculate ConsistencyIndex, PlaceRate, experience metrics  
**Affects All Dogs**: Yes - every dog has these as 0

#### Recent Form (10 factors) - ALL MISSING
5. **Last3TimesSec** → [] (empty list, not in PDF)
6. **Margins** → [] (empty list, not in PDF)
7. **RecentWinRate** → 0 (can't calculate without Last3Times)
8. **StreakLength** → 0 (can't calculate without Margins)
9. **FormTrend** → 0 (can't calculate without Last3Times)
10. **FormMomentum** → 0 (can't calculate without Margins)
11. **PerformanceStability** → 0 (can't calculate without Last3Times)
12. **RecoveryRate** → 0 (can't calculate without form history)
13. **PeakPerformance** → 0 (can't calculate without Last3Times)
14. **FormConsistency** → 0 (can't calculate without Last3Times)

**Why Not Working**: PDFs don't include recent race history  
**Impact**: Can't assess momentum, trends, consistency  
**Affects All Dogs**: Yes - every dog missing form data

#### Connections (6 factors) - MOSTLY MISSING
15. **Trainer** → Unknown/missing (not reliably in PDF)
16. **Owner** → Unknown/missing (not reliably in PDF)
17. **Sire** → Unknown/missing (not in PDF)
18. **Dam** → Unknown/missing (not in PDF)
19. **TrainerStrikeRate** → 0 (can't lookup without Trainer name)
20. **OwnerSuccess** → 0 (can't lookup without Owner name)

**Why Not Working**: PDFs don't include connection data  
**Impact**: Can't assess trainer/owner quality  
**Affects All Dogs**: Yes - every dog missing connections

#### Derived Speed Metrics (8 factors) - PARTIALLY WORKING
21. **Speed_kmh** → Calculated BUT same for identical times
22. **EarlySpeedIndex** → Calculated BUT same for identical sectionals
23. **AvgSpeed** → 0 (needs Last3TimesSec)
24. **MaxSpeed** → Same as BestTimeSec (no comparison)
25. **SpeedConsistency** → 0 (needs Last3TimesSec for std dev)
26. **SpeedImprovement** → 0 (needs Last3TimesSec for trend)
27. **RelativeSpeed** → Calculated BUT when all same, all equal
28. **SpeedPercentile** → Calculated BUT compressed when similar

**Why Not Working**: Missing historical speed data  
**Impact**: Can calculate current speed but not trends/consistency  
**Affects Dogs With Identical Times**: Severely (5 dogs at 13.6s)

#### Derived Consistency Metrics (8 factors) - NOT WORKING
29. **ConsistencyIndex** → 0/0 = undefined (needs CareerWins/Starts)
30. **PlaceRate** → 0/0 = undefined (needs CareerPlaces/Starts)
31. **FinishConsistency** → 0 (needs Last3TimesSec)
32. **FormTrend** → 0 (needs Last3TimesSec)
33. **RecentPlaceRate** → 0 (needs recent place history)
34. **WinPercentage** → 0 (needs CareerWins)
35. **PlacePercentage** → 0 (needs CareerPlaces)
36. **ROIRating** → 0 (needs PrizeMoney and outcomes)

**Why Not Working**: Missing career and form data  
**Impact**: Can't assess reliability, consistency  
**Affects All Dogs**: Yes - every dog

#### Derived Experience Metrics (8 factors) - NOT WORKING
37. **RestFactor** → Calculated from DLR (WORKING)
38. **BoxBiasFactor** → Calculated from Box (WORKING)
39. **DistanceSuit** → 0 (needs historical performance at distance)
40. **TrackExperience** → 0 (needs races at this track)
41. **GradeExperience** → 0 (needs races in this grade)
42. **ExperienceIndex** → Uses CareerStarts (all 0 or default)
43. **AdaptabilityScore** → 0 (needs performance across conditions)
44. **VeteranBonus** → 0 (needs age + experience combination)

**Why Not Working**: Missing historical racing data  
**Impact**: Can't assess suitability, experience advantage  
**Affects All Dogs**: Yes, though RestFactor and BoxBiasFactor work

#### Derived Competitive Metrics (6 factors) - NOT WORKING
45. **FieldStrength** → Can calculate BUT all same when opponents unknown
46. **RelativeClass** → 0 (needs historical performance comparison)
47. **OpponentQuality** → 0 (needs opponent history)
48. **CompetitiveEdge** → 0 (needs head-to-head data)
49. **ClassAdvantage** → 0 (needs grade performance history)
50. **PaceAdvantage** → Partial (needs more than just sectional)

**Why Not Working**: Missing competitive history  
**Impact**: Can't assess relative strength vs field  
**Affects All Dogs**: Yes

### 🟡 PARTIALLY WORKING (20-25 Factors)

#### Timing Data (2 factors) - WORKS WHEN VARIES
51. **BestTimeSec** ✓ Present in PDF
   - **Issue**: 5 dogs have IDENTICAL 13.6s
   - **When Works**: Villified (11.9s) vs others (13.6s) = CLEAR diff
   - **When Fails**: 5 dogs at 13.6s = NO differentiation

52. **SectionalSec** ✓ Present in PDF
   - **Issue**: 5 dogs have IDENTICAL 13.6s
   - **When Works**: Villified (11.9s) vs others (13.6s) = CLEAR diff
   - **When Fails**: 5 dogs at 13.6s = NO differentiation

**Impact**: MASSIVE when times differ, ZERO when times identical

#### Physical Attributes (4 factors) - LIMITED VARIANCE
53. **Age** ✓ Present (30-45 months range)
   - **Variance**: Small (15 month spread)
   - **Impact**: Limited differentiation (~5% weight max)

54. **Weight** ✓ Present (29-34 kg range)
   - **Variance**: Small (5 kg spread)
   - **Impact**: Limited differentiation (~5% weight max)

55. **Sex** ✓ Present (M/D)
   - **Variance**: Binary only
   - **Impact**: Minimal differentiation

56. **Color** ✓ Present but not used
   - **Variance**: Multiple values
   - **Impact**: Zero (not included in scoring)

#### Rest/Draw (2 factors) - WORKS
57. **DLR** ✓ Present (5-14 days range)
   - **Variance**: Good (9 day spread)
   - **Impact**: Moderate (~10% weight)
   - **Works Well**: Clear differentiation

58. **Draw** ✓ Present
   - **Variance**: Good (1-8)
   - **Impact**: Small (~2% weight)

#### Race Context (4 factors) - CONSTANT PER RACE
59. **Distance** ✓ Present (520m for Race 7)
   - **Variance**: None (same for all dogs in race)
   - **Impact**: Zero for differentiation within race

60. **Grade** ✓ Present (Grade 5)
   - **Variance**: None (same for all dogs in race)
   - **Impact**: Zero for differentiation within race

61. **Track** ✓ Present (Wentworth Park)
   - **Variance**: None (same for all dogs in race)
   - **Impact**: Zero for differentiation within race

62. **RaceDate** ✓ Present
   - **Variance**: None (same for all dogs in race)
   - **Impact**: Zero for differentiation within race

### 🟢 WORKING WELL (5-10 Factors)

63. **Box** ✅ ALWAYS VARIES (1-8)
   - **Variance**: Excellent (each dog different)
   - **Impact**: HIGH (~20% weight)
   - **Reliability**: 100%

64. **BestTimeSec** ✅ WHEN DIFFERENT
   - **Variance**: Excellent when varies (11.9 vs 13.6)
   - **Impact**: HIGHEST (~31% weight)
   - **Reliability**: High for Villified, zero for 5 identical dogs

65. **SectionalSec** ✅ WHEN DIFFERENT
   - **Variance**: Excellent when varies
   - **Impact**: HIGH (~26% weight)
   - **Reliability**: High for Villified, zero for 5 identical dogs

66. **DLR** ✅ ALWAYS VARIES
   - **Variance**: Good (5-14 days)
   - **Impact**: MODERATE (~10% weight)
   - **Reliability**: 100%

67. **Age** ✅ ALWAYS VARIES
   - **Variance**: Limited but present
   - **Impact**: SMALL (~5% weight)
   - **Reliability**: 100%

68. **Weight** ✅ ALWAYS VARIES
   - **Variance**: Limited but present
   - **Impact**: SMALL (~5% weight)
   - **Reliability**: 100%

69. **BoxBiasFactor** ✅ DERIVED FROM BOX
   - **Variance**: Excellent (based on box)
   - **Impact**: Included in Box weight
   - **Reliability**: 100%

70. **RestFactor** ✅ DERIVED FROM DLR
   - **Variance**: Good (based on DLR)
   - **Impact**: Included in DLR weight
   - **Reliability**: 100%

**Total Working**: 8 factors with clear variance

---

## Part 2: Per-Dog Analysis - Race 7

### Box 1 - Quick Thinkin' (Score: 9.10%)

#### ✅ WORKING Factors (8)
- Box: 1 (inside advantage)
- BestTimeSec: 13.6s (average)
- SectionalSec: 13.6s (average)
- DLR: 7 days (optimal)
- Age: 36 months
- Weight: 31 kg
- BoxBiasFactor: High (inside box)
- RestFactor: Optimal (7 days)

#### ❌ NOT WORKING Factors (40-45)
- CareerWins: 0
- CareerPlaces: 0
- PrizeMoney: 0
- Last3TimesSec: []
- Margins: []
- Trainer: Unknown
- Owner: Unknown
- ConsistencyIndex: 0
- FormMomentum: 0
- TrainerStrikeRate: 0
- PlaceRate: undefined
- FinishConsistency: 0
- FormTrend: 0
- SpeedConsistency: 0
- DistanceSuit: 0
- TrackExperience: 0
- [30+ more zero/missing]

**Score Limited By**: Only 8 factors differentiate this dog

### Box 2 - Elite Whisper (Score: 10.20%)

#### ✅ WORKING Factors (8)
- Box: 2
- BestTimeSec: 13.6s (IDENTICAL to Box 1)
- SectionalSec: 13.6s (IDENTICAL to Box 1)
- DLR: 7 days
- Age: 35 months (-1 vs Box 1)
- Weight: 32 kg (+1 vs Box 1)
- BoxBiasFactor: High
- RestFactor: Optimal

#### ❌ NOT WORKING Factors (40-45)
- [Same as Box 1 - all missing]

**Score Difference from Box 1**: 1.1% (only due to Box position, tiny age/weight diff)

### Box 7 - Villified (Score: 45.42%) ⭐

#### ✅ WORKING Factors (8)
- Box: 7 (wide box disadvantage)
- BestTimeSec: 11.9s ⭐ (1.7s FASTER - HUGE!)
- SectionalSec: 11.9s ⭐ (1.7s FASTER - HUGE!)
- DLR: 7 days (optimal)
- Age: 36 months
- Weight: 32 kg
- BoxBiasFactor: Low (wide box penalty)
- RestFactor: Optimal

#### ❌ NOT WORKING Factors (40-45)
- [Same as Box 1 - all missing]

**Why High Score**: 
- BestTime 1.7s faster = DOMINANT speed advantage
- Overcomes wide box disadvantage
- BUT lacks validation (no form history, career stats)
- Can't confirm if consistent or one-time fluke

**Risk**: Without career/form data, high score based ONLY on speed
- If dog has poor record → speed might be outlier
- If dog is consistent → speed is reliable
- **We don't know which!**

---

## Part 3: Impact Analysis

### When Times Are Identical (5 Dogs)

**Dogs Affected**:
- Box 1 - Quick Thinkin': 13.6s
- Box 2 - Elite Whisper: 13.6s
- Box 3 - Gloria Keeping: 13.6s
- Box 6 - Spring Drop: 13.6s
- Box 8 - Cawbourne Don: 13.6s

**Only Differentiators**:
1. Box position (1, 2, 3, 6, 8)
2. DLR (7, 7, 14, 10, 7 days)
3. Age (small variance)
4. Weight (small variance)

**Result**: Scores compress to 2.81-10.20% range (7.4% spread)
- Without speed variance, only Box/DLR matter
- 40+ missing factors can't contribute
- Limited differentiation

### When Times Differ (Villified vs Others)

**Villified**: 11.9s (MUCH faster)
**Others**: 13.6s or 13.1s

**Result**: Villified scores 45.42% (dominant)
- Speed difference = 1.7s (14% faster)
- Overcomes all other factors
- Clear favorite

**BUT**: Missing 40+ validation factors
- Can't verify consistency
- Can't check career record
- Can't assess form trend
- High risk if speed is outlier

---

## Part 4: What Needs Fixing

### Priority 1: Extract Career Stats (4 factors)

**Target Features**:
- CareerStarts
- CareerWins
- CareerPlaces
- PrizeMoney

**Where to Find in PDF**:
- Usually in career summary section
- Format: "12 Starts, 5 Wins, 8 Places, $45,000"
- May be in table or text

**Expected Impact**:
- Enables ConsistencyIndex (win rate)
- Enables PlaceRate
- Enables experience metrics
- +10 derived features become useful

**Example**:
- Villified with 5 wins/12 starts = 42% win rate (EXCELLENT)
- vs Quick Thinkin' with 2 wins/20 starts = 10% win rate (POOR)
- Would validate Villified's high score

### Priority 2: Extract Form Data (2 features → 10+ derived)

**Target Features**:
- Last3TimesSec: [time1, time2, time3]
- Margins: [margin1, margin2, margin3]

**Where to Find in PDF**:
- Recent form section
- Last 3-5 races table
- Format: "11.95(+2.5), 12.10(-0.5), 12.00(+1.0)"

**Expected Impact**:
- Enables FinishConsistency
- Enables FormMomentum
- Enables FormTrend
- Enables SpeedConsistency
- +15 derived features become useful

**Example**:
- Villified times: [11.9, 12.1, 12.0] = consistent (std 0.10)
- vs Quick Thinkin' times: [13.6, 14.2, 13.8] = inconsistent (std 0.31)
- Would show Villified is reliably fast

### Priority 3: Extract Connections (2 features → 6+ derived)

**Target Features**:
- Trainer name
- Owner name

**Where to Find in PDF**:
- Header section
- Dog details
- Format: "Trainer: John Smith, Owner: ABC Racing"

**Expected Impact**:
- Enables TrainerStrikeRate lookup
- Enables OwnerSuccess lookup
- Context for dog quality
- +4 derived features

**Example**:
- Villified's trainer with 25% strike rate = GOOD
- vs Quick Thinkin's trainer with 10% strike rate = POOR
- Additional validation

### Priority 4: Improve Time Parsing

**Current Issue**: 5 dogs with identical 13.6s
- Real data OR parsing error?
- Need hundredths precision

**Fix**:
- Parse to 2 decimal places (13.63 vs 13.68)
- Verify truly identical vs rounding
- Extract more granular times if available

**Expected Impact**:
- Better differentiation when times close
- More accurate speed metrics
- Reduced score compression

---

## Part 5: Expected Improvements

### Current State
- **Working Factors**: 5-10
- **Missing Factors**: 40-45
- **Score Range** (identical times): 2.8-10.2% (7.4% spread)
- **Score Range** (with speed diff): 2.8-45.4% (42.6% spread)
- **Reliability**: Low (missing validation)

### After Priority 1 (Career Stats)
- **Working Factors**: 10-15
- **Missing Factors**: 35-40
- **Score Range**: 5-35% (expected)
- **Reliability**: Medium (some validation)
- **Time**: 2-3 days to implement

### After Priority 2 (Form Data)
- **Working Factors**: 20-25
- **Missing Factors**: 25-30
- **Score Range**: 8-40% (expected)
- **Reliability**: Medium-High (good validation)
- **Time**: +3-5 days

### After Priority 3 (Connections)
- **Working Factors**: 25-30
- **Missing Factors**: 20-25
- **Score Range**: 10-45% (expected)
- **Reliability**: High (comprehensive validation)
- **Time**: +1-2 days

### After Priority 4 (Better Parsing)
- **Working Factors**: 25-30 (same)
- **Missing Factors**: 20-25 (same)
- **Score Range**: 12-48% (expected - better spread)
- **Reliability**: High (same)
- **Time**: +1 day

### Final Expected State
- **Working Factors**: 25-30 (vs 5-10 now)
- **Missing Factors**: 20-25 (vs 40-45 now)
- **Improvement**: 3-4x more usable features
- **Score Range**: 12-48% (vs 7.4-42.6% now)
- **Reliability**: HIGH (comprehensive data)

---

## Part 6: Summary for User

### Question: "Which factors are still not working for each dog?"

### Answer:

**NOT WORKING** (40-45 factors):
- Career statistics (Wins, Places, Money)
- Form history (Last 3 times, Margins)
- Connections (Trainer, Owner, Breeding)
- All derived metrics depending on above

**PARTIALLY WORKING** (20-25 factors):
- BestTimeSec (works when differs, fails when identical)
- SectionalSec (works when differs, fails when identical)
- Age, Weight, DLR (limited variance)
- Race context (constant within race)

**WORKING WELL** (5-10 factors):
- Box position (always varies)
- Times (when they differ between dogs)
- DLR (good variance)
- RestFactor, BoxBiasFactor (derived from above)

### Impact Per Dog:

**Every dog affected the same way**:
- Missing same 40-45 factors
- Limited to 5-10 differentiating factors
- Heavy reliance on speed times
- No career/form validation

**Special Cases**:
- **Villified**: High score due to speed (45.42%) but lacks validation
- **5 dogs at 13.6s**: Scores compress (2.8-10.2%) due to identical times

### How to Fix:

**4-Phase Approach**:
1. Extract career stats (2-3 days) → +10 working factors
2. Extract form data (3-5 days) → +15 working factors
3. Extract connections (1-2 days) → +6 working factors
4. Improve time parsing (1 day) → better differentiation

**Total Time**: 7-11 days
**Result**: 25-30 working factors (vs 5-10 now), 3-4x improvement

### Bottom Line:

**Current System**: Limited by missing data
- Only 5-10 factors actually work
- 40-45 factors are zeros/defaults
- Score differentiation relies heavily on speed
- No validation of performance reliability

**After Fixes**: Comprehensive analysis
- 25-30 factors working
- Career and form validation
- More reliable predictions
- Better score spread
- Higher confidence in selections

**User now knows EXACTLY which factors are missing and how they affect each dog.**
