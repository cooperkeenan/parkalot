import logging
from datetime import datetime

from .log_storage import LOG_FORMAT, RunLogCapture, save_run_log

# Log to the console (visible in the container logs) and capture the run's
# log so it can be saved to Blob Storage when the run ends.
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
# The Azure SDK logs every HTTP request at INFO level; keep only its problems.
logging.getLogger("azure").setLevel(logging.WARNING)
run_log = RunLogCapture()
logging.getLogger().addHandler(run_log)

# Import the main function
from . import main

# Create a dummy timer request object
class DummyTimerRequest:
    def __init__(self):
        self.past_due = False

if __name__ == "__main__":
    try:
        logging.info(f"Running ReserveParkalot at {datetime.utcnow()} UTC")
        timer = DummyTimerRequest()
        main(timer)
        logging.info("ReserveParkalot completed")
    except BaseException:
        logging.exception("ReserveParkalot crashed with an unhandled error")
        raise
    finally:
        save_run_log(run_log)
