import os
import time
import logging
from datetime import datetime, timedelta

import azure.functions as func
from playwright.sync_api import sync_playwright


def main(mytimer: func.TimerRequest) -> None:
    # -------------------------------------------------------------------
    # 1) Pull credentials (swap out for secure storage in production)
    # -------------------------------------------------------------------
    email = os.environ.get("PARKALOT_USER", "ckeenan@craneware.com")
    password = os.environ.get("PARKALOT_PASS", "ApolloTheGreat!0")

    # -------------------------------------------------------------------
    # 2) Calculate next Sunday (for testing). Build both "8th June" and "8 June".
    # -------------------------------------------------------------------
    today = datetime.utcnow()
    days_ahead = 6 - today.weekday()  # Sunday = 6
    if days_ahead <= 0:
        days_ahead += 7
    next_sunday = today + timedelta(days=days_ahead)
    day_number = next_sunday.day
    month = next_sunday.strftime("%B")
    possible_texts = [f"{day_number}th {month}", f"{day_number} {month}"]

    try:
        # ------------------------------------------------------------
        # 3) Launch headless Chromium, navigate to login page
        # ------------------------------------------------------------
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            logging.info("➡️ Navigating to login page...")
            page.goto("https://app.parkalot.io/login/", timeout=60000)

            # Give the page a moment to start loading
            time.sleep(1)

            logging.info("🔍 Waiting for email field...")
            page.wait_for_selector('input[type="email"]', timeout=15000)

            logging.info(f"✏️ Filling email: {email}")
            page.fill('input[type="email"]', email)

            logging.info("✏️ Filling password (hidden)...")
            page.fill('input[type="password"]', password)

            logging.info("🖱 Clicking LOG IN button...")
            page.click('button:has-text("LOG IN")')

            # ------------------------------------------------------------
            # 4) Wait for the “/client” URL and for the “UPCOMING” button
            # ------------------------------------------------------------
            logging.info("⏳ Waiting for dashboard URL (/client)...")
            page.wait_for_url("**/client", timeout=20000)
            logging.info(f"✅ Logged in! Current URL: {page.url}")

            # Extra small delay to let post-login scripts finish
            time.sleep(2)

            logging.info("🔍 Waiting for ‘UPCOMING’ button to confirm dashboard is ready...")
            page.wait_for_selector('button:has-text("UPCOMING")', timeout=20000)
            logging.info("✅ ‘UPCOMING’ button found.")

            # ------------------------------------------------------------
            # 5) Click “ALL DAYS” so that next-week cards are visible
            # ------------------------------------------------------------
            logging.info("🖱 Clicking ‘ALL DAYS’ to reveal full calendar...")
            page.click('button:has-text("ALL DAYS")', timeout=10000)

            # Instead of waiting for a box-color selector (which can be flaky),
            # just sleep a few seconds to let the UI render all day-cards on screen.
            logging.info("⏳ Pausing 5 seconds for calendar to finish rendering...")
            time.sleep(5)

            # ------------------------------------------------------------
            # 6) Grab all “day-cards” by looking for the shared box-color class
            # ------------------------------------------------------------
            cards = page.locator('div[class*="box-color"]')
            num_cards = cards.count()
            logging.info(f"🗂 Found {num_cards} day-cards on the page.")
            time.sleep(1)

            found_reservation = False

            for i in range(num_cards):
                card = cards.nth(i)
                card_text = card.inner_text().strip()
                lower_text = card_text.lower()

                # Check if this card’s text contains one of our target date strings
                if any(txt.lower() in lower_text for txt in possible_texts):
                    logging.info(f"▶ Found matching card (index {i}) for {possible_texts!r}:")
                    logging.info(f"   {card_text.replace(chr(10), ' | ')}")

                    # --------------------------------------------------------
                    # 7) Within this card, look for “RESERVE”
                    # --------------------------------------------------------
                    reserve_buttons = card.locator('button:has-text("RESERVE")')
                    count_btns = reserve_buttons.count()
                    logging.info(f"   🔘 {count_btns} button(s) inside this card.")

                    for j in range(count_btns):
                        btn = reserve_buttons.nth(j)
                        btn_text = btn.inner_text().strip()
                        logging.info(f"    Button {j} text: {btn_text!r}")

                        if "reserve" in btn_text.lower():
                            # ------------------------------------------------
                            # 8) Force-click “RESERVE” via JS (no scroll/hover)
                            # ------------------------------------------------
                            logging.info(
                                f"    🖱 Force-clicking ‘RESERVE’ (card {i}, button {j})..."
                            )
                            btn.evaluate("el => el.click()")

                            # ------------------------------------------------
                            # 9) After clicking, pause so the UI has time to update
                            # ------------------------------------------------
                            time.sleep(8)

                            # ------------------------------------------------
                            # 10) Wait a few seconds to see if “RELEASE” appears
                            # ------------------------------------------------
                            try:
                                card.wait_for_selector(
                                    'button:has-text("RELEASE")', timeout=8000
                                )
                                logging.info(
                                    "    ✅ RELEASE appeared—reservation likely succeeded."
                                )
                            except Exception:
                                logging.warning(
                                    "    ⚠️ RELEASE did NOT appear in this card. Booking may have failed."
                                )

                            # ------------------------------------------------
                            # 11) Take a full-page screenshot so you can inspect
                            # ------------------------------------------------
                            screenshot_path = os.path.join(os.getcwd(), "after_reserve.png")
                            page.screenshot(path=screenshot_path, full_page=True)
                            logging.info(f"    📸 Screenshot saved to {screenshot_path!r}\n")

                            found_reservation = True
                            break  # break out of the “buttons” loop

                    if found_reservation:
                        break  # break out of the “cards” loop
                    else:
                        logging.info(f"    ℹ️ No “RESERVE” clicked in card {i}, moving on.")

            if not found_reservation:
                # ------------------------------------------------------------
                # 12) If no “RESERVE” was clicked, grab a debug screenshot
                # ------------------------------------------------------------
                logging.error(f"❌ Could not find a “RESERVE” button for {possible_texts!r}.")
                debug_path = os.path.join(os.getcwd(), "debug_fullpage.png")
                page.screenshot(path=debug_path, full_page=True)
                logging.info(f"    📸 Debug screenshot saved to {debug_path!r}")

            browser.close()

    except Exception as e:
        logging.error(f"❌ Unexpected error in main(): {e}")
