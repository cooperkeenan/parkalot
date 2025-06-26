# notification_service.py

import os
import logging
from abc import ABC, abstractmethod
from typing import List
from twilio.rest import Client
from twilio.base.exceptions import TwilioException


class INotificationService(ABC):
    """Interface for sending notifications about reservation status"""
    
    @abstractmethod
    def send_success_notification(self, target_dates: List[str], parking_spot: str = None) -> bool:
        """Send notification when reservation is successful"""
        pass
    
    @abstractmethod
    def send_failure_notification(self, target_dates: List[str], error_message: str = None) -> bool:
        """Send notification when reservation fails"""
        pass


class TwilioNotificationService(INotificationService):
    """Twilio SMS implementation of notification service"""
    
    def __init__(self, account_sid: str = None, auth_token: str = None, 
                 from_number: str = None, to_number: str = None):
        """
        Initialize Twilio service with credentials
        
        Args:
            account_sid: Twilio account SID (defaults to env var TWILIO_SID)
            auth_token: Twilio auth token (defaults to env var TWILIO_AUTH_TOKEN)  
            from_number: Twilio phone number (defaults to env var TWILIO_FROM_NUMBER)
            to_number: Recipient phone number (defaults to env var TWILIO_TO_NUMBER)
        """
        self._account_sid = account_sid or os.environ.get("TWILIO_SID")
        self._auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN")
        self._from_number = from_number or os.environ.get("TWILIO_FROM_NUMBER")
        self._to_number = to_number or os.environ.get("TWILIO_TO_NUMBER")
        
        if not all([self._account_sid, self._auth_token, self._from_number, self._to_number]):
            missing = []
            if not self._account_sid: missing.append("TWILIO_SID")
            if not self._auth_token: missing.append("TWILIO_AUTH_TOKEN")
            if not self._from_number: missing.append("TWILIO_FROM_NUMBER")
            if not self._to_number: missing.append("TWILIO_TO_NUMBER")
            raise ValueError(f"Missing required Twilio environment variables: {', '.join(missing)}")
        
        self._client = Client(self._account_sid, self._auth_token)
    
    def send_success_notification(self, target_dates: List[str], parking_spot: str = None) -> bool:
        """Send success SMS notification"""
        dates_str = " or ".join(target_dates)
        if parking_spot:
            message = f"✅ Parkalot SUCCESS: Parking spot {parking_spot} reserved for {dates_str}!"
        else:
            message = f"✅ Parkalot SUCCESS: Parking reservation confirmed for {dates_str}!"
        return self._send_sms(message)
    
    def send_failure_notification(self, target_dates: List[str], error_message: str = None) -> bool:
        """Send failure SMS notification"""
        dates_str = " or ".join(target_dates)
        message = f"❌ Parkalot FAILED: Could not reserve parking for {dates_str}."
        if error_message:
            message += f" Error: {error_message}"
        return self._send_sms(message)
    
    def _send_sms(self, message: str) -> bool:
        """
        Send SMS message via Twilio
        
        Args:
            message: SMS message content
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        try:
            logging.info(f"Sending SMS notification to {self._to_number}")
            
            message_obj = self._client.messages.create(
                body=message,
                from_=self._from_number,
                to=self._to_number
            )
            
            logging.info(f"SMS sent successfully. SID: {message_obj.sid}")
            return True
            
        except TwilioException as e:
            logging.error(f"Twilio error sending SMS: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending SMS: {e}")
            return False


class LogOnlyNotificationService(INotificationService):
    """Fallback notification service that only logs messages"""
    
    def send_success_notification(self, target_dates: List[str], parking_spot: str = None) -> bool:
        """Log success message only"""
        dates_str = " or ".join(target_dates)
        if parking_spot:
            logging.info(f"SUCCESS NOTIFICATION: Parking spot {parking_spot} reserved for {dates_str}")
        else:
            logging.info(f"SUCCESS NOTIFICATION: Parking reservation confirmed for {dates_str}")
        return True
    
    def send_failure_notification(self, target_dates: List[str], error_message: str = None) -> bool:
        """Log failure message only"""
        dates_str = " or ".join(target_dates)
        message = f"FAILURE NOTIFICATION: Could not reserve parking for {dates_str}"
        if error_message:
            message += f". Error: {error_message}"
        logging.warning(message)
        return True