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
        next_date = today + timedelta(days=7)
        
        # Skip weekends
        if next_date.weekday() == 5:  # Saturday
            next_date = next_date + timedelta(days=2)  # Move to Monday
        elif next_date.weekday() == 6:  # Sunday
            next_date = next_date + timedelta(days=1)  # Move to Monday
        
        day_number = next_date.day
        month_name = next_date.strftime("%B")
        
        # Get the correct ordinal suffix
        ordinal_suffix = self._get_ordinal_suffix(day_number)
        
        return [f"{day_number}{ordinal_suffix} {month_name}", f"{day_number} {month_name}"]
        #return ["29th June", "29 June"]
    
    def _get_ordinal_suffix(self, day: int) -> str:
        """Return the ordinal suffix for a given day number."""
        if 11 <= day <= 13:  # Special case for 11th, 12th, 13th
            return "th"
        elif day % 10 == 1:  # 1st, 21st, 31st
            return "st"
        elif day % 10 == 2:  # 2nd, 22nd
            return "nd"
        elif day % 10 == 3:  # 3rd, 23rd
            return "rd"
        else:  # Everything else gets "th"
            return "th"

