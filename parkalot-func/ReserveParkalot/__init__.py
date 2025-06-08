# __init__.py

import logging
import azure.functions as func
from .coordinator import (
    get_credentials,
    get_target_dates, 
    create_services,
    start_browser,
    wait_for_reservation_time,
    refresh_calendar,
    cleanup_browser
)
from .login_service import ILoginService, LoginService
from .date_calculator import IDateCalculator, DateService
from .reservation_service import IReservationService, ReservationService
from .verification_service import IVerificationService, VerificationService


def main(mytimer: func.TimerRequest) -> None:
    """Main entry point showing high-level reservation process"""
    logging.info("=== ReserveParkalot timer trigger started ===")
    
    #  Get environment setup
    email, password = get_credentials()
    if not email or not password:
        return
    
    #  Create all services using dependency injection
    date_calculator, login_service, reservation_service, verification_service = create_services(email, password)
    target_texts = get_target_dates(date_calculator)
    
    # Start browser session
    playwright_instance, browser, page = start_browser()
    
    try:
        # Login
        login_service.login(page)
        
        # Wait until 12:00:02
        wait_for_reservation_time()
        
        # Refresh page 
        refresh_calendar(page)
        
        # Attempt to reserve parking spot
        reservation_service.reserve(page, target_texts)
        
        # Verify reservation was successful
        verification_result = verification_service.verify(page, target_texts)
        
        # Log final result
        if verification_result:
            logging.info("SUCCESS: Parking reservation completed and verified")
        else:
            logging.warning("FAILED: Parking reservation could not be verified")
            
    except Exception as e:
        logging.error(f"Reservation process failed: {e}")
        
    finally:
        # cleanup resources
        cleanup_browser(playwright_instance, browser)
    
    logging.info("=== ReserveParkalot timer trigger completed ===")