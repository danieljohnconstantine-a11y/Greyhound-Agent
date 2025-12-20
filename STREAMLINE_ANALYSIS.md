# Streamline Analysis - Files That Can Be Deleted

## Analysis Date: 2025-12-20

### Files Identified for Deletion

#### 1. Empty/Placeholder Files
**train_ml_model.py** (0 bytes)
- Status: EMPTY FILE
- Reason: Completely empty, no code
- Replacement: `train_ml_enhanced.py` is the actual implementation
- **Recommendation: DELETE**

#### 2. Duplicate/Obsolete Test Files
**tests/test_exporter.py** (933 bytes)
- Status: Tests legacy exporter (moved to legacy/)
- Module: Tests `legacy/exporter.py` which is archived
- No longer needed as exporter functionality replaced by excel_export.py
- **Recommendation: DELETE**

**tests/test_scorer.py** (933 bytes)
- Status: Tests old scorer implementation
- Module: Tests legacy scorer (now replaced by src/scorer.py)
- The new scorer.py is different and used by run_complete_analysis.py
- **Recommendation: DELETE** (old test for old implementation)

**tests/test_parser.py** (933 bytes)
- Status: Duplicate of test_parser_simple.py
- Note: All three files (test_exporter, test_scorer, test_parser) appear to be identical copies
- **Recommendation: DELETE** (we have test_parser_simple.py and test_integration.py)

#### 3. Legacy Directory (Optional - Already Archived)
**legacy/** directory (5 files + README)
- config.py, diagnostic.py, exporter.py, extract.py, utils.py
- Status: Already archived with documentation
- Purpose: Preserved for reference
- No imports from any active code
- **Recommendation: KEEP** (already properly archived with README explaining purpose)
  - Alternative: DELETE if you're confident you won't need reference

#### 4. Redundant Batch Files (Optional)
**run_main.bat** (31 bytes)
- Content: Just runs `python main.py` and `pause`
- Status: Very simple wrapper
- **Recommendation: KEEP** (provides convenience for Windows users)

**run_parser.bat** (127 bytes)  
- Content: Runs parser with data/*.pdf
- Status: Simple wrapper for common task
- **Recommendation: KEEP** (useful for Windows users)

#### 5. Documentation Files to Review
**CHANGES.md** (3,678 bytes)
- Status: Change log/history
- **Recommendation: KEEP** (documents repository evolution)

**PIPELINE_TEST_REPORT.md** (3,588 bytes)
- Status: Test results from pipeline verification
- **Recommendation: KEEP** (documents that system works, valuable for users)

### Summary of Deletions

**Definite Deletions (High Confidence):**
1. `train_ml_model.py` - Empty file, replaced by train_ml_enhanced.py
2. `tests/test_exporter.py` - Tests archived legacy code
3. `tests/test_scorer.py` - Tests old scorer implementation
4. `tests/test_parser.py` - Duplicate test file

**Total Space Saved:** ~2.8 KB (minimal, but removes clutter)

**Optional Deletions (If you want maximum minimalism):**
5. `legacy/` directory (entire folder) - 5 archived files + README
   - Only if certain you won't need reference to old code
   - Space saved: ~7 KB

### Files to KEEP

**Core Pipeline:**
- main.py, src/*.py (9 modules)

**ML Training:**
- train_ml_enhanced.py, train_ml_enhanced.bat
- run_complete_analysis.py, run_complete_analysis.bat

**Batch Helpers:**
- run_predictions_today.bat, run_main.bat, run_parser.bat, train_ml.bat

**Tests:**
- test_integration.py (functional tests)
- test_parser_simple.py (basic parser test)
- debug_parser.py (debugging utility)

**Documentation:**
- README.md, CHANGES.md, PIPELINE_TEST_REPORT.md
- data_predictions/README.md, models/README.md, legacy/README.md

**Data:**
- All data/ PDFs and CSVs (needed for ML training)
- data_predictions/ structure (for daily workflow)

### Recommendation

**Conservative Approach (Recommended):**
Delete only the 4 definite files (train_ml_model.py + 3 obsolete test files)
- Minimal risk
- Removes clear redundancy
- Keeps legacy/ for reference

**Aggressive Approach:**
Delete the 4 files + entire legacy/ directory
- Maximum cleanliness
- Assumes no need for old code reference
- Saves ~10 KB total

