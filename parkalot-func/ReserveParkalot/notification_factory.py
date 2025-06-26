# notification_factory.py

import os
import logging
from .notification_service import INotificationService, TwilioNotificationService, LogOnlyNotificationService


class NotificationFactory:
    """Factory for creating notification service instances"""
    
    @staticmethod
    def create_notification_service() -> INotificationService:
        """
        Create appropriate notification service based on available configuration
        
        Returns:
            INotificationService: TwilioNotificationService if credentials available,
                                 LogOnlyNotificationService as fallback
        """
        try:
            # Check if all Twilio environment variables are present
            required_vars = ["TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "TWILIO_TO_NUMBER"]
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            
            if missing_vars:
                logging.warning(f"Missing Twilio environment variables: {', '.join(missing_vars)}")
                logging.warning("Falling back to log-only notifications")
                return LogOnlyNotificationService()
            
            # All variables present, create Twilio service
            logging.info("Creating Twilio notification service")
            return TwilioNotificationService()
            
        except Exception as e:
            logging.error(f"Error creating Twilio notification service: {e}")
            logging.warning("Falling back to log-only notifications")
            return LogOnlyNotificationService()