#!/bin/bash

# Ensure script stops on error
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

echo "Starting pipeline..."

# 1. Run 24h Scan
echo "Running 24h scan..."
python3 run_scan.py

# 2. Run Positioning
echo "Running positioning analysis..."
# Assuming scan saves to datasets/24h_accrued as per default behavior
python3 -m agenti.cli run --dataset datasets/24h_accrued --output agenti/output/positioning_plan.json

echo "Pipeline completed successfully."
