#!/bin/bash

echo "Starting Parkalot container..."
echo "Current time: $(date)"
echo "Environment variables set:"
env | grep PARKALOT

# write out our cron job (with env vars baked in)
cat <<EOF > /etc/cron.d/parkalot-cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PARKALOT_USER=$PARKALOT_USER
PARKALOT_PASS=$PARKALOT_PASS
12 20 * * *   root    /app/run_reservation.sh
EOF

chmod 0644 /etc/cron.d/parkalot-cron

echo "Cron job created with environment variables:"
cat /etc/cron.d/parkalot-cron

# start cron and then tail the log so the container doesn't exit
cron
echo "Waiting for cron job…"
tail -f /var/log/parkalot.log
