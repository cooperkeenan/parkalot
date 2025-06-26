# verification_service.py

import os
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from playwright.sync_api import Page


class IVerificationService(ABC):
    @abstractmethod
    def verify(self, page: Page, target_date_texts: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify reservation and return success status and parking spot number
        
        Returns:
            Tuple[bool, Optional[str]]: (success, parking_spot_number)
        """
        pass


class VerificationService(IVerificationService):
    def verify(self, page: Page, target_date_texts: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify reservation and extract parking spot number
        
        Returns:
            Tuple[bool, Optional[str]]: (success, parking_spot_number)
        """
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

                # Extract parking spot number from the card
                parking_spot = self._extract_parking_spot_number(card, card_text)
                
                # Look for RELEASE button to confirm booking
                try:
                    release_button = card.locator('button:has-text("RELEASE")')
                    release_button.wait_for(timeout=8000)
                    found_text = release_button.inner_text().strip()
                    logging.info(f"RELEASE button found with text: {found_text}")
                    
                    if parking_spot:
                        logging.info(f"Successfully extracted parking spot number: {parking_spot}")
                    else:
                        logging.warning("Could not extract parking spot number from reservation card")
                    
                    return True, parking_spot
                    
                except Exception:
                    logging.warning("RELEASE button not found. Booking may have failed")
                    return False, None

        # No matching reservation found
        logging.error(f"No reservation card found matching {target_date_texts}")
        return False, None
    
    def _extract_parking_spot_number(self, card_element, card_text: str) -> Optional[str]:
        """
        Extract parking spot number from reservation card
        
        Args:
            card_element: Playwright locator for the card
            card_text: Full text content of the card
            
        Returns:
            Optional[str]: Parking spot number (e.g., "126", "126a") or None if not found
        """
        try:
            # Method 1: Look for span with class "text_600" (the number before "booked")
            number_spans = card_element.locator('span[class*="text_600"]')
            if number_spans.count() > 0:
                for i in range(number_spans.count()):
                    span_text = number_spans.nth(i).inner_text().strip()
                    # Check if this span contains a number (could be followed by letter like 126a)
                    if re.match(r'^\d+[a-zA-Z]*$', span_text):
                        logging.info(f"Found parking spot number in span: {span_text}")
                        return span_text
            
            # Method 2: Look for patterns in the card text
            # Pattern: number followed by optional letter, then "booked" or similar
            patterns = [
                r'(\d+[a-zA-Z]*)\s*(?:booked|reserved)',  # "126 booked" or "126a booked"
                r'(?:spot|space|bay)\s*(\d+[a-zA-Z]*)',   # "spot 126" or "space 126a"
                r'(\d+[a-zA-Z]*)\s*(?:-|–|—)',           # "126 -" or "126a -"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, card_text, re.IGNORECASE)
                if match:
                    spot_number = match.group(1)
                    logging.info(f"Found parking spot number using pattern '{pattern}': {spot_number}")
                    return spot_number
            
            # Method 3: Fallback - look for any standalone number in the card
            # This is less reliable but better than nothing
            numbers = re.findall(r'\b\d+[a-zA-Z]*\b', card_text)
            if numbers:
                # Filter out obvious non-parking-spot numbers (like years, times)
                filtered_numbers = [num for num in numbers if not re.match(r'^(19|20)\d{2}$', num)]  # Not years
                filtered_numbers = [num for num in filtered_numbers if not re.match(r'^[0-2]\d:[0-5]\d$', num)]  # Not times
                
                if filtered_numbers:
                    spot_number = filtered_numbers[0]  # Take first remaining number
                    logging.info(f"Found parking spot number using fallback method: {spot_number}")
                    return spot_number
            
            logging.warning("Could not extract parking spot number from card")
            logging.debug(f"Card text for debugging: {card_text}")
            return None
            
        except Exception as e:
            logging.error(f"Error extracting parking spot number: {e}")
            return None