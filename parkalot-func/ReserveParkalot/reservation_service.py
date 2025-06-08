# reservation_service.py

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import List
from playwright.sync_api import Page


class IReservationService(ABC):

    @abstractmethod
    def reserve(self, page: Page, target_date_texts: List[str]) -> bool:
        pass


class ReservationService(IReservationService):
    def reserve(self, page: Page, target_date_texts: List[str]) -> bool:
        # Click ALL DAYS to reveal full calendar
        logging.info("Clicking 'ALL DAYS' to reveal full calendar")
        page.click('button:has-text("ALL DAYS")', timeout=10000)

        # Wait for calendar to render
        logging.info("Pausing 5 seconds for calendar to finish rendering")
        time.sleep(5)

        # Get all day cards
        cards = page.locator('div[class*="box-color"]')
        num_cards = cards.count()
        logging.info(f"Found {num_cards} day cards on the page")

        # Check each card for target date
        for i in range(num_cards):
            card = cards.nth(i)
            card_text = card.inner_text().strip()
            lower_card_text = card_text.lower()

            if any(txt.lower() in lower_card_text for txt in target_date_texts):
                logging.info(f"Found matching card (index {i}) for {target_date_texts}")
                logging.info(f"Card text: {card_text.replace(chr(10), ' | ')}")

                # Look for RESERVE buttons in this card
                reserve_buttons = card.locator('button:has-text("RESERVE")')
                count_btns = reserve_buttons.count()
                logging.info(f"{count_btns} button(s) inside this card")

                # Try to click each RESERVE button
                for j in range(count_btns):
                    btn = reserve_buttons.nth(j)
                    btn_text = btn.inner_text().strip()
                    logging.info(f"Button {j} text: {btn_text}")

                    if "reserve" in btn_text.lower():
                        logging.info(f"Force-clicking 'RESERVE' (card {i}, button {j})")
                        btn.evaluate("el => el.click()")

                        # Wait for UI to update
                        time.sleep(4)

                        return True

                logging.info(f"No RESERVE clicked in card {i}, moving on")

        # No RESERVE button found or clicked
        logging.error(f"Could not find a RESERVE button for any of {target_date_texts}")
        return False