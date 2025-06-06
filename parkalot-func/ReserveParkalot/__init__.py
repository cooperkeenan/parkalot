import os
import time
import logging
from datetime import datetime, timedelta

import azure.functions as func
from playwright.sync_api import sync_playwright

def main(mytimer: func.TimerRequest) -> None:
    logging.info("=== ReserveParkalot timer trigger started ===")

    # 1) Credentials
    email    = os.environ["PARKALOT_USER"]
    password = os.environ["PARKALOT_PASS"]

    # 2) Hard-code for testing: Sunday the 8th
    target_texts = ["8th June", "8 June"]
    logging.info(f"Target date texts: {target_texts!r}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page    = browser.new_page()

            # 3) Login + land on the calendar
            page.goto("https://app.parkalot.io/login/", timeout=60000)
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.click('button:has-text("LOG IN")')
            page.wait_for_url("**/client", timeout=20000)
            logging.info("✅ Logged in, at /client")

            # Reveal next-week cards
            time.sleep(2)
            page.click('button:has-text("ALL DAYS")')
            logging.info("⏳ Waiting 5 s for calendar render…")
            time.sleep(5)

            # 4) WAIT UNTIL 12:00:02
            now    = datetime.now()
            target = now.replace(hour=12, minute=0, second=2, microsecond=0)
            if now < target:
                wait_secs = (target - now).total_seconds()
                logging.info(f"🕐 Sleeping {wait_secs:.1f}s until 12:00:02…")
                time.sleep(wait_secs)

            # 5) REFRESH page right at 12:00:02
            logging.info("🔄 Reloading page to open reservation window…")
            page.reload()
            time.sleep(1)

            # 6) Find & click “RESERVE” (same as before)
            cards = page.locator('div[class*="box-color"]')
            for i in range(cards.count()):
                card = cards.nth(i)
                text = card.inner_text().lower()
                if any(t.lower() in text for t in target_texts):
                    logging.info(f"▶ Day-card #{i}: {card.inner_text().replace(chr(10),' | ')}")
                    btns = card.locator('button:has-text("RESERVE")')
                    if btns.count():
                        logging.info(f"    🖱 Clicking RESERVE…")
                        btns.nth(0).evaluate("el => el.click()")
                        time.sleep(8)
                        page.screenshot(path="after_reserve.png", full_page=True)
                    break

            # 7) VERIFY as before (navigate to My Reservations…)
            page.click('button:has-text("MY RESERVATIONS")')
            time.sleep(5)
            res_cards = page.locator('div[class*="box-color"]')
            for j in range(res_cards.count()):
                rc = res_cards.nth(j)
                txt = rc.inner_text().lower()
                if any(t.lower() in txt for t in target_texts):
                    if rc.locator('button:has-text("RELEASE")').count():
                        logging.info("✅ RELEASE found — reservation succeeded!")
                    else:
                        logging.error("❌ Found card but no RELEASE inside it.")
                    break

            browser.close()

    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")

    logging.info("=== ReserveParkalot timer trigger completed ===")
