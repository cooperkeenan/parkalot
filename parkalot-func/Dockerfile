FROM mcr.microsoft.com/playwright/python:v1.41.0-focal

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ReserveParkalot/ ./ReserveParkalot/

# Run once and exit (NO CRON)
CMD ["python", "-m", "ReserveParkalot"]