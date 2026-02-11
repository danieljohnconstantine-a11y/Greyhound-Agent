@echo off
REM Simple script to merge ML files to clean branch
echo ========================================
echo Merging ML files to clean branch
echo ========================================
echo.

git fetch origin clean
git fetch origin copilot/copy-ml-training-prediction-files
git checkout clean
git merge origin/copilot/copy-ml-training-prediction-files -m "Merge ML files from streamline-repo-structure"
git push origin clean

echo.
echo ========================================
echo DONE! Files are now on clean branch
echo ========================================
pause
