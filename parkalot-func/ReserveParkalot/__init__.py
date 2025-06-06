import os
import time
import logging
from datetime import datetime, timedelta

import azure.functions as func
from playwright.sync_api import sync_playwright

def main(mytimer: func.TimerRequest) -> None:
    logging.info("=== ReserveParkalot timer trigger started ===")

    # 1) Credentials
    email = os.environ.get("PARKALOT_USER", "ckeenan@craneware.com")
    password = os.environ.get("PARKALOT_PASS", "ApolloTheGreat!0")

    # 2) Hard-code for testing: Sunday the 8th
    target_texts = ["8th June", "8 June"]
    logging.info(f"Target date texts for reservation: {target_texts!r}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 3) Log in
            logging.info("➡️  Navigating to login page…")
            page.goto("https://app.parkalot.io/login/", timeout=60000)
            page.wait_for_selector('input[type="email"]', timeout=15000)
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.click('button:has-text("LOG IN")')
            page.wait_for_url("**/client", timeout=20000)
            logging.info(f"✅  Logged in! URL: {page.url}")

            # 4) Reveal next-week cards
            time.sleep(2)
            page.wait_for_selector('button:has-text("UPCOMING")', timeout=20000)
            page.click('button:has-text("ALL DAYS")')
            logging.info("⏳  Waiting 5s for calendar to render…")
            time.sleep(5)

            # 5) Find & click “RESERVE”
            cards = page.locator('div[class*="box-color"]')
            for i in range(cards.count()):
                card = cards.nth(i)
                text = card.inner_text().lower()
                if any(t.lower() in text for t in target_texts):
                    logging.info(f"▶ Found day-card #{i}: {card.inner_text().replace(chr(10), ' | ')}")
                    btns = card.locator('button:has-text("RESERVE")')
                    if btns.count() > 0:
                        logging.info(f"    🖱 Force-clicking RESERVE on card {i}")
                        btns.nth(0).evaluate("el => el.click()")
                        time.sleep(8)
                        page.screenshot(path="after_reserve.png", full_page=True)
                        logging.info("    📸 after_reserve.png")
                        break
            else:
                logging.error("❌  No RESERVE button found for our date")
                page.screenshot(path="debug_fullpage.png", full_page=True)
                browser.close()
                return

            logging.info("✅  Reserve clicked. Now verifying…")

            # 6) Verify in My Reservations
            page.click('button:has-text("MY RESERVATIONS")')
            logging.info("🖱  Navigating to My Reservations…")
            time.sleep(5)

            res_cards = page.locator('div[class*="box-color"]')
            for j in range(res_cards.count()):
                rc = res_cards.nth(j)
                txt = rc.inner_text().lower()
                if any(t.lower() in txt for t in target_texts):
                    logging.info(f"▶ Found reservation card #{j}: {txt.replace(chr(10), ' | ')}")
                    if rc.locator('button:has-text("RELEASE")').count() > 0:
                        logging.info("🎉  RELEASE button present — reservation verified!")
                    else:
                        logging.error("❌  Found our card but no RELEASE button inside it")
                        page.screenshot(path="after_verify.png", full_page=True)
                    break
            else:
                logging.error("❌  Never found a reservation card matching our date")
                page.screenshot(path="after_verify.png", full_page=True)

            browser.close()

    except Exception as e:
        logging.error(f"❌ Unexpected error in main(): {e}")

    logging.info("=== ReserveParkalot timer trigger completed ===")
