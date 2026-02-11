#!/bin/bash
# Script to push clean branch to origin
# Run this with: GH_TOKEN=<your-token> bash push_clean_branch.sh

set -e

echo "========================================"
echo "Pushing clean branch to origin/clean"
echo "========================================"
echo ""

CLEAN_SHA=$(git rev-parse clean)
echo "Clean branch SHA: $CLEAN_SHA"
echo ""

if [ -z "$GH_TOKEN" ]; then
    echo "ERROR: GH_TOKEN environment variable not set"
    echo "Please run: GH_TOKEN=<your-token> bash push_clean_branch.sh"
    exit 1
fi

echo "Updating refs/heads/clean on GitHub..."
curl -X PATCH \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/danieljohnconstantine-a11y/Greyhound-Agent/git/refs/heads/clean \
  -d "{\"sha\":\"$CLEAN_SHA\",\"force\":true}"

echo ""
echo "========================================"
echo "DONE! Clean branch pushed to origin"
echo "========================================"
