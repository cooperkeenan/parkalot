import logging
import azure.functions as func
from playwright.sync_api import sync_playwright
import os

def main(mytimer: func.TimerRequest) -> None:
    logging.info('Python timer trigger function ran at %s', mytimer.schedule_status.last)

    # Fetch credentials securely (replace with os.environ in production)
    email = os.environ.get('PARKALOT_USER', 'ckeenan@craneware.com')
    password = os.environ.get('PARKALOT_PASS', 'ApolloTheGreat!0')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://app.parkalot.io/login/")  
            page.fill("#email", email)
            page.fill("#password", password)
            page.click("#login-button")
            browser.close()
        logging.info('Reservation completed successfully!')
    except Exception as e:
        logging.error(f"Error occurred: {e}")
