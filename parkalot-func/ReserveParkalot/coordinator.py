# coordinator.py

import os
import time
import logging
from datetime import datetime, time as dtime, timezone
from playwright.sync_api import sync_playwright, Page, Browser

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.8 in the Docker image
    from backports.zoneinfo import ZoneInfo

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


# Parkalot releases spaces at 12:00 UK time. Using the Europe/London time zone
# means this follows the clocks changing (GMT in winter, BST in summer).
UK_TZ = ZoneInfo("Europe/London")
BOOKING_OPENS_UK = dtime(12, 0, 6)  # a few seconds after opening


# Work out how long to wait until booking opens today, in UK time
def seconds_until_booking_opens(now_utc: datetime):
    now_uk = now_utc.astimezone(UK_TZ)
    target_uk = datetime.combine(now_uk.date(), BOOKING_OPENS_UK, tzinfo=UK_TZ)
    target_utc = target_uk.astimezone(timezone.utc)
    return (target_utc - now_utc).total_seconds(), target_utc


# Wait until booking opens (12:00:06 UK time) if ACTIVE is True
def wait_for_reservation_time():
    if not ACTIVE:
        logging.info("ACTIVE=False: Skipping wait, running immediately for testing")
        return

    wait_secs, target_utc = seconds_until_booking_opens(datetime.now(timezone.utc))
    opens_uk = BOOKING_OPENS_UK.strftime("%H:%M:%S")
    if wait_secs > 0:
        logging.info(
            f"Sleeping for {wait_secs:.0f}s until {opens_uk} UK time "
            f"({target_utc:%H:%M:%S} UTC)"
        )
        time.sleep(wait_secs)
    else:
        # Started late: try now rather than waiting until tomorrow
        logging.warning(
            f"Run started {-wait_secs / 60:.1f} minutes after booking opened at "
            f"{opens_uk} UK time ({target_utc:%H:%M:%S} UTC); trying immediately. "
            "Check the Logic App start time."
        )


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