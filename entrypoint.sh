#!/bin/bash
set -e

echo "Starting Parkalot container..."
echo "Current time: $(date)"
echo "Environment variables set:"
env | grep -E 'PARKALOT|PLAYWRIGHT_BROWSERS_PATH' || true
echo

# Make sure the log file exists
touch /var/log/parkalot.log

# Run the reservation script immediately
echo "Running reservation script immediately..."
cd /app
export PYTHONPATH=/app
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Run the script and capture output
python -m ReserveParkalot 2>&1 | tee /var/log/parkalot.log

echo "Reservation script completed at $(date)"
echo "Exit code: $?"

# Keep container alive for a bit to allow log viewing
echo "Keeping container alive for 2 minutes for log access..."
sleep 120
