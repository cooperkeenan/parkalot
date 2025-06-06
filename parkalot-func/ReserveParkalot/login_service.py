# login_service.py

import time
import logging
from abc import ABC, abstractmethod
from playwright.sync_api import Page


class ILoginService(ABC):
    """
    Single responsibility: log into Parkalot and wait for the dashboard to be ready.
    """
    @abstractmethod
    def login(self, page: Page) -> None:
        pass


class LoginService(ILoginService):
    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password

    def login(self, page: Page) -> None:
        logging.info("➡️  Navigating to login page...")
        page.goto("https://app.parkalot.io/login/", timeout=60000)

        # Short pause so inputs begin to render
        time.sleep(1)

        logging.info("🔍  Waiting for email field...")
        page.wait_for_selector('input[type="email"]', timeout=15000)

        logging.info(f"✏️  Filling email: {self._email}")
        page.fill('input[type="email"]', self._email)

        logging.info("✏️  Filling password (hidden)...")
        page.fill('input[type="password"]', self._password)

        logging.info("🖱  Clicking LOG IN button...")
        page.click('button:has-text("LOG IN")')

        logging.info("⏳  Waiting for dashboard URL (/client)...")
        page.wait_for_url("**/client", timeout=20000)
        logging.info(f"✅  Logged in! Current URL: {page.url}")

        # Wait for client‐side scripts to finish
        time.sleep(2)

        logging.info("🔍  Waiting for ‘UPCOMING’ button to confirm dashboard is ready...")
        page.wait_for_selector('button:has-text("UPCOMING")', timeout=20000)
        logging.info("✅  ‘UPCOMING’ button found.")
