# verification_service.py

import os
import logging
from abc import ABC, abstractmethod
from typing import List
from playwright.sync_api import Page


class IVerificationService(ABC):
    @abstractmethod
    def verify(self, page: Page, target_date_texts: List[str]) -> bool:
        pass


class VerificationService(IVerificationService):
    def verify(self, page: Page, target_date_texts: List[str]) -> bool:
        # Navigate to My Reservations section
        logging.info("Clicking 'MY RESERVATIONS' to view existing bookings")
        page.click('button:has-text("MY RESERVATIONS")', timeout=10000)

        # Wait for reservation cards to load
        logging.info("Waiting for reservation cards to appear")
        reservations = page.locator('div[class*="box-color"]')
        reservations.first.wait_for(state="visible", timeout=20000)
        num_res = reservations.count()
        logging.info(f"Found {num_res} reservation cards in My Reservations")

        # Check each reservation card for target date
        for idx in range(num_res):
            card = reservations.nth(idx)
            card_text = card.inner_text().strip()
            lower_card_text = card_text.lower()

            if any(txt.lower() in lower_card_text for txt in target_date_texts):
                logging.info(f"Matched reservation card (index {idx}): "f"{card_text.replace(chr(10), ' | ')}")

                # Look for RELEASE button to confirm booking
                try:
                    release_button = card.locator('button:has-text("RELEASE")')
                    release_button.wait_for(timeout=8000)
                    found_text = release_button.inner_text().strip()
                    logging.info(f"RELEASE button found with text: {found_text}")
                    return True
                except Exception:
                    logging.warning("RELEASE button not found. Booking may have failed")
                    return False

        # No matching reservation found
        logging.error(f"No reservation card found matching {target_date_texts}")
        return False