import azure.functions as func
import datetime
import json
import logging
import os
from logging.handlers import RotatingFileHandler

log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'parkalot.log')

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Create file handler with rotation (10MB max, keep 5 backup files)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

root_logger.addHandler(file_handler)

logging.info("File logging initialized at: %s", log_file)

app = func.FunctionApp()