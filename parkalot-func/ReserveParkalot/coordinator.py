# coordinator.py

import os
import time
import logging
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, Page, Browser

from .login_service import ILoginService, LoginService
from .date_calculator import IDateCalculator, DateService
from .reservation_service import IReservationService, ReservationService
from .verification_service import IVerificationService, VerificationService
from .notification_service import INotificationService
from .notification_factory import NotificationFactory


# Change to False to avoid wait times for testing
ACTIVE = True

# Get email and password from environment variables
def get_credentials():
    try:
        email = os.environ["PARKALOT_USER"]
        password = os.environ["PARKALOT_PASS"]
        return email, password
    except KeyError as e:
        logging.error(f"Missing env var {e.args[0]}; aborting")
        return None, None


# Get the target date texts for reservation
def get_target_dates(date_calculator: IDateCalculator = None):
    if date_calculator is None:
        date_calculator = DateService()
    
    target_texts = date_calculator.get_target_date_texts()
    logging.info(f"Target date texts for reservation: {target_texts}")
    return target_texts
    

# Create all service instances with dependency injection
def create_services(email: str, password: str):
    date_calculator: IDateCalculator = DateService()
    login_service: ILoginService = LoginService(email, password)
    reservation_service: IReservationService = ReservationService()
    verification_service: IVerificationService = VerificationService()
    notification_service: INotificationService = NotificationFactory.create_notification_service()
    
    return date_calculator, login_service, reservation_service, verification_service, notification_service


# Start Playwright browser and return browser and page objects
def start_browser():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    return p, browser, page


# Wait until 11:00:01 UTC (12:00:01 UK time) if ACTIVE is True
def wait_for_reservation_time():
    if ACTIVE:
        now = datetime.utcnow()
        # Set to 11:00:01 UTC (12:00:01 UK BST)
        target_time = now.replace(hour=11, minute=0, second=13, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)
        wait_secs = (target_time - now).total_seconds()
        logging.info(f"Sleeping for {wait_secs:.0f}s until {target_time.time()} UTC (12:00:01 UK time)")
        time.sleep(wait_secs)
    else:
        logging.info("ACTIVE=False: Skipping wait, running immediately for testing")


# Reload the calendar page
def refresh_calendar(page: Page):
    logging.info("Reloading calendar page")
    page.reload()


# Close browser and cleanup Playwright
def cleanup_browser(playwright_instance, browser: Browser):
    browser.close()
    playwright_instance.stop()


# LOOKING FOR WRONG DATE
# 2025-06-16 11:00:21,529 - root - ERROR - Could not find a RESERVE button for any of ['23th June', '23 June']