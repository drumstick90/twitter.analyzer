#!/bin/bash

# Get current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create log directory
mkdir -p "$DIR/logs"

# Add cron job to run daily at 6:00 AM UTC
# We use a temporary file to avoid messing up existing crontab
crontab -l > mycron 2>/dev/null || true
echo "0 6 * * * cd $DIR && ./run_pipeline.sh >> $DIR/logs/pipeline.log 2>&1" >> mycron
crontab mycron
rm mycron

echo "Cron job added to run daily at 6:00 AM UTC."
echo "Logs will be written to $DIR/logs/pipeline.log"
