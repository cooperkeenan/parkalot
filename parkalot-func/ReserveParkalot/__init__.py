import logging
import azure.functions as func
from .coordinator import run

def main(mytimer: func.TimerRequest) -> None:
    logging.info("=== ReserveParkalot timer trigger started ===")
    run()
    logging.info("=== ReserveParkalot timer trigger completed ===")
