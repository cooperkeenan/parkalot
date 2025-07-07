#!/bin/bash
set -e

echo "Starting Parkalot container..."
echo "Current time: $(date)"
echo "Environment variables set:"
env | grep -E 'PARKALOT|PLAYWRIGHT_BROWSERS_PATH|TWILIO' || true
echo

# Make sure the log file exists
touch /var/log/parkalot.log

# ------------------------------------------------------------------------------
# Build the cron-file with all variables the job will need
# ------------------------------------------------------------------------------
cat > /etc/cron.d/parkalot-cron <<CRON
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
PARKALOT_USER=${PARKALOT_USER}
PARKALOT_PASS=${PARKALOT_PASS}
TWILIO_SID=${TWILIO_SID:-}
TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN:-}
TWILIO_FROM_NUMBER=${TWILIO_FROM_NUMBER:-}
TWILIO_TO_NUMBER=${TWILIO_TO_NUMBER:-}
57 10 * * *   root  /app/run_reservation.sh
CRON

chmod 0644 /etc/cron.d/parkalot-cron

echo "Cron job created with environment variables:"
cat /etc/cron.d/parkalot-cron
echo

# ------------------------------------------------------------------------------
# Start cron in the background, then tail the log so the container keeps running
# ------------------------------------------------------------------------------
cron
echo "Waiting for cron job..."
tail -f /var/log/parkalot.log