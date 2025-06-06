# verification_service.py

import os
import logging
from abc import ABC, abstractmethod
from typing import List
from playwright.sync_api import Page


class IVerificationService(ABC):
    """
    Single responsibility: after attempting a reservation, navigate to “My Reservations”
    and verify that the same date‐card now shows a “RELEASE” button.
    """
    @abstractmethod
    def verify(self, page: Page, target_date_texts: List[str]) -> bool:
        pass


class VerificationService(IVerificationService):
    def verify(self, page: Page, target_date_texts: List[str]) -> bool:
        """
        1) Click “MY RESERVATIONS” in the dashboard.
        2) Wait for reservation cards to appear.
        3) For each reservation card, if its inner_text contains target_date_texts:
           a) check if a “RELEASE” button is present inside that card
           b) return True if found; otherwise screenshot and return False.
        4) If no matching card is found at all, screenshot and return False.
        """
        logging.info("🖱  Clicking ‘MY RESERVATIONS’ to view existing bookings…")
        page.click('button:has-text("MY RESERVATIONS")', timeout=10000)

        logging.info("🔍  Waiting for reservation cards to appear…")
        reservations = page.locator('div[class*="box-color"]')
        reservations.wait_for(count=1, timeout=20000)
        num_res = reservations.count()
        logging.info(f"🔍  Found {num_res} reservation cards in “My Reservations.”")

        for idx in range(num_res):
            card = reservations.nth(idx)
            card_text = card.inner_text().strip()
            lower_card_text = card_text.lower()

            if any(txt.lower() in lower_card_text for txt in target_date_texts):
                logging.info(f"    ▶ Matched reservation card (index {idx}): "
                             f"{card_text.replace(chr(10), ' | ')}")

                try:
                    release_button = card.locator('button:has-text("RELEASE")')
                    release_button.wait_for(timeout=8000)
                    found_text = release_button.inner_text().strip()
                    logging.info(f"     ✅ RELEASE button was found with text: {found_text!r}")
                    return True
                except Exception:
                    logging.warning("     ⚠️ RELEASE did NOT appear in this card. Booking may have silently failed.")
                    debug_path = os.path.join(os.getcwd(), "after_reserve.png")
                    page.screenshot(path=debug_path, full_page=True)
                    logging.info(f"     📸 Screenshot saved to {debug_path!r}")
                    return False

        logging.error(f"❌ Did not find any reservation card matching {target_date_texts!r} in “My Reservations.”")
        bug_path = os.path.join(os.getcwd(), "bug_my_reservations.png")
        page.screenshot(path=bug_path, full_page=True)
        logging.info(f"    📸 Screenshot saved to {bug_path!r}")
        return False
