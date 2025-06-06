# reservation_service.py

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import List
from playwright.sync_api import Page


class IReservationService(ABC):
    """
    Single responsibility: find the correct date‐card for next week and click “RESERVE.”
    Returns True if “RESERVE” was clicked successfully.
    """
    @abstractmethod
    def reserve(self, page: Page, target_date_texts: List[str]) -> bool:
        pass


class ReservationService(IReservationService):
    def reserve(self, page: Page, target_date_texts: List[str]) -> bool:
        """
        1) Click “ALL DAYS” to reveal next‐week cards.
        2) Grab all day‐cards via `div[class*="box-color"]`.
        3) For each card, if its inner_text contains one of target_date_texts:
           a) find the “RESERVE” button inside that card
           b) force‐click it via JS
           c) wait 8 seconds, take a screenshot, and return True
        4) If no card matched or no button clicked, take a debug screenshot and return False.
        """
        logging.info("🖱  Clicking ‘ALL DAYS’ to reveal full calendar...")
        page.click('button:has-text("ALL DAYS")', timeout=10000)

        logging.info("⏳  Pausing 5 seconds for calendar to finish rendering...")
        time.sleep(5)

        cards = page.locator('div[class*="box-color"]')
        num_cards = cards.count()
        logging.info(f"🗂  Found {num_cards} day‐cards on the page.")

        for i in range(num_cards):
            card = cards.nth(i)
            card_text = card.inner_text().strip()
            lower_card_text = card_text.lower()

            if any(txt.lower() in lower_card_text for txt in target_date_texts):
                logging.info(f"▶ Found matching card (index {i}) for {target_date_texts!r}:")
                logging.info(f"   {card_text.replace(chr(10), ' | ')}")

                reserve_buttons = card.locator('button:has-text("RESERVE")')
                count_btns = reserve_buttons.count()
                logging.info(f"   🔘 {count_btns} button(s) inside this card.")

                for j in range(count_btns):
                    btn = reserve_buttons.nth(j)
                    btn_text = btn.inner_text().strip()
                    logging.info(f"    Button {j} text: {btn_text!r}")

                    if "reserve" in btn_text.lower():
                        logging.info(f"    🖱 Force‐clicking ‘RESERVE’ (card {i}, button {j})...")
                        btn.evaluate("el => el.click()")

                        # Pause to let the UI update
                        time.sleep(4)

                        # Take a screenshot after clicking
                        screenshot_path = os.path.join(os.getcwd(), "after_reserve.png")
                        page.screenshot(path=screenshot_path, full_page=True)
                        logging.info(f"    📸 Screenshot saved to {screenshot_path!r}\n")

                        return True

                logging.info(f"    ℹ️ No “RESERVE” clicked in card {i}, moving on.")

        # No “RESERVE” button clicked
        logging.error(f"❌ Could not find a “RESERVE” button for any of {target_date_texts!r}.")
        debug_path = os.path.join(os.getcwd(), "debug_fullpage.png")
        page.screenshot(path=debug_path, full_page=True)
        logging.info(f"    📸 Debug screenshot saved to {debug_path!r}")
        return False
