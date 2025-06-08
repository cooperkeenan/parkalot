import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the main function
from . import main

# Create a dummy timer request object
class DummyTimerRequest:
    def __init__(self):
        self.past_due = False

if __name__ == "__main__":
    logging.info(f"Running ReserveParkalot at {datetime.utcnow()} UTC")
    timer = DummyTimerRequest()
    main(timer)
    logging.info("ReserveParkalot completed")