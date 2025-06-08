# coordinator.py

import os
import time
import logging
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

from .login_service      import LoginService
from .date_calculator    import DateService
from .reservation_service import ReservationService
from .verification_service import VerificationService


# flip this to False to completely disable the live‐noon wait & reserve run
ACTIVE = False

def run():
    if not ACTIVE:
        logging.warning("Coordinator is inactive; skipping reservation run.")
        return

    # ——— 1) gather creds & target dates —————————————————————————
    try:
        email = os.environ["PARKALOT_USER"]
        password = os.environ["PARKALOT_PASS"]
    except KeyError as e:
        logging.error(f"Missing env var {e.args[0]}; aborting")
        return

    date_service = DateService()
    target_texts = date_service.get_target_texts()
    logging.info(f"Target date texts for reservation: {target_texts}")

    # ——— 2) spin up browser & do login ——————————————————————————
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        LoginService(email, password).login(page)

        # ——— 3) optionally wait until 12:00:02 UTC —————————————————
        now = datetime.utcnow()
        target_time = now.replace(hour=12, minute=0, second=2, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)
        wait_secs = (target_time - now).total_seconds()
        logging.info(f"Sleeping for {wait_secs:.0f}s until {target_time.time()} UTC")
        time.sleep(wait_secs)

        # after the wait, make sure we have the fresh calendar
        logging.info("⟲ reload calendar page")
        page.reload()

        # ——— 4) try to reserve & verify —————————————————————————
        ReservationService().reserve(page, target_texts)
        ok = VerificationService().verify(page, target_texts)
        logging.info("✅ Reservation verified" if ok else "❌ Reservation failed")

        browser.close()
