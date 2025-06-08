# Use the “playwright/python” base (which already includes the browser binaries)
FROM mcr.microsoft.com/playwright/python:v1.41.0-focal

# Make sure Playwright will look in the bundled location
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install cron
RUN apt-get update \
 && apt-get install -y cron \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install any extra Python deps you have
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY ReserveParkalot/ ./ReserveParkalot/

# Copy your two scripts
COPY run_reservation.sh entrypoint.sh ./

RUN chmod +x run_reservation.sh entrypoint.sh \
 && touch /var/log/parkalot.log

# Start cron (with your job pointing at run_reservation.sh) and tail the log
CMD ["./entrypoint.sh"]
