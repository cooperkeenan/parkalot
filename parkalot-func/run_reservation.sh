#!/bin/bash
# go to app root and ensure modules are on PYTHONPATH
cd /app
export PYTHONPATH=/app

# kick off the reservation flow
python -m ReserveParkalot >> /var/log/parkalot.log 2>&1
