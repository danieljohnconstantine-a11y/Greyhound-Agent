# Legacy Code

This directory contains legacy/unused code from previous versions of the Greyhound Analytics pipeline.

## Files

- **config.py** - Old configuration file with scoring weights (not used in current pipeline)
- **diagnostic.py** - PDF diagnostic tool for debugging parsing issues
- **exporter.py** - Old Excel export function (replaced by CSV exports in main.py)
- **extract.py** - PDF text extraction utility (functionality now in main.py)
- **utils.py** - Utility functions for environment setup (not used in current pipeline)

## Why These Files Are Here

These files were part of earlier versions of the codebase but are no longer used by the main pipeline (`main.py`). They have been moved here to keep the `src/` directory clean and focused on actively used code, while preserving these files for:

1. Historical reference
2. Potential future use
3. Debugging and diagnostics

## Current Active Code

The current working pipeline consists of:
- `main.py` (root) - Main pipeline orchestration
- `src/parser.py` - Race form parsing logic
- `src/features.py` - Feature computation and scoring
