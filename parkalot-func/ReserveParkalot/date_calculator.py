# date_calculator.py

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List

# Date calculator Interface
class IDateCalculator(ABC):
    @abstractmethod
    def get_target_date_texts(self) -> List[str]:
        pass


# Calculate date one week from now 
class DateService(IDateCalculator):
    def get_target_date_texts(self) -> List[str]:

        # Calculate the same weekday but one week ahead of today.

        today = datetime.utcnow()
        # To get next week's “same weekday,” just add 7 days
        next_date = today + timedelta(days=7)
        day_number = next_date.day
        month_name = next_date.strftime("%B")
        return [f"{day_number}th {month_name}", f"{day_number} {month_name}"]
        #return ["8th June", "8 June"]


