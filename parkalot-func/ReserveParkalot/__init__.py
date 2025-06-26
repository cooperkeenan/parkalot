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
from .notification_service import INotificationService


def main(mytimer: func.TimerRequest) -> None:
    """Main entry point showing high-level reservation process"""
    logging.info("=== ReserveParkalot timer trigger started ===")
    
    #  Get environment setup
    email, password = get_credentials()
    if not email or not password:
        return
    
    #  Create all services using dependency injection
    date_calculator, login_service, reservation_service, verification_service, notification_service = create_services(email, password)
    target_texts = get_target_dates(date_calculator)
    
    # Start browser session
    playwright_instance, browser, page = start_browser()
    
    reservation_success = False
    verification_success = False
    error_message = None
    
    try:
        # Login
        login_service.login(page)
        
        # Wait until 12:00:02
        wait_for_reservation_time()
        
        # Refresh page 
        refresh_calendar(page)
        
        # Attempt to reserve parking spot
        reservation_success = reservation_service.reserve(page, target_texts)
        
        if reservation_success:
            # Verify reservation was successful and get parking spot number
            verification_success, parking_spot = verification_service.verify(page, target_texts)
            
            # Log final result
            if verification_success:
                if parking_spot:
                    logging.info(f"SUCCESS: Parking spot {parking_spot} reserved and verified")
                else:
                    logging.info("SUCCESS: Parking reservation completed and verified")
                notification_service.send_success_notification(target_texts, parking_spot)
            else:
                logging.warning("FAILED: Parking reservation could not be verified")
                error_message = "Reservation appeared to succeed but could not be verified"
                notification_service.send_failure_notification(target_texts, error_message)
        else:
            logging.error("FAILED: Could not make parking reservation")
            error_message = "Could not find or click RESERVE button"
            notification_service.send_failure_notification(target_texts, error_message)
            
    except Exception as e:
        logging.error(f"Reservation process failed: {e}")
        error_message = str(e)
        notification_service.send_failure_notification(target_texts, error_message)
        
    finally:
        # cleanup resources
        cleanup_browser(playwright_instance, browser)
    
    logging.info("=== ReserveParkalot timer trigger completed ===")