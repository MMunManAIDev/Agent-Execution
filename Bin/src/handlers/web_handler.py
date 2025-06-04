"""
Web Handler Module

Beheert alle web-gerelateerde interacties via Selenium WebDriver.
"""

import os
import time
import json
import logging
import asyncio

from typing import Optional, Tuple, Dict, Any
from playwright.async_api import async_playwright
from urllib.parse import urlparse, urlunparse
from PIL import Image

from ..config import Config
from ..utils.constants import STATUS_CODES  # Direct import van constants

def clean_url(url: str) -> str:
    # Parse the URL to separate components
    parsed = urlparse(url)

    # If no scheme is provided, default to https
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)  # Re-parse the updated URL to ensure all components are captured

    # Remove 'www' prefix if it exists
    if parsed.hostname and parsed.hostname.startswith('www.'):
        hostname_without_www = parsed.hostname[4:]  # Remove the 'www.' prefix
        parsed = parsed._replace(netloc=hostname_without_www)

    # Reconstruct and return the cleaned URL
    return urlunparse(parsed)

class WebPageHandler:
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.logger = logging.getLogger(__name__)
        self.load_lock = asyncio.Lock()
        
    async def start_browser(self):
        """Start the Playwright browser session asynchronously."""
        try:
            self.playwright = await async_playwright().start()  # Use async_playwright instead of sync_playwright
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            logging.getLogger(__name__).info("Playwright browser session started successfully")
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to start Playwright browser: {str(e)}")
        
    async def load_page(self, url: str) -> bool:
        # Use the lock to prevent multiple loads at the same time
        async with self.load_lock:
            try:
                # Ensure URL starts with http:// or https://
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = f'https://{url}'

                # Log that page load is starting
                self.logger.info(f"Loading page: {url}")

                # Attempt to navigate to the URL
                await self.page.goto(url, timeout=60000)  # Timeout after 60 seconds if the page doesn't load

                # Wait for the page to be fully loaded - network idle
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)  # Optional delay to ensure rendering is complete
                self.logger.info("Page loaded successfully")

                # Check the response status
                response_status = self.page.evaluate("document.readyState")
                if response_status != "complete":
                    self.logger.warning(f"Page load incomplete for: {url}")

                return True

            except TimeoutError:
                self.logger.error(f"Failed to load page (Timeout): {url}")
                return False

            except Exception as e:
                self.logger.error(f"Failed to load page: {str(e)}")
                return False

    async def get_snapshot(self, filename: str) -> bool:
        try:
            # Create the screenshot directory if it does not exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Take a screenshot of the current page
            await self.page.screenshot(path=filename, full_page=True)
            self.logger.info(f"Snapshot saved at {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to take snapshot: {str(e)}")
            return False

    def perform_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Voer een actie uit op de webpagina.
        
        Args:
            action: Dictionary met actie informatie
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            action_type = action.get('type', '').upper()
            target = action.get('target', '')
            value = action.get('value', '')

            # Log de actie
            self.logger.info(f"Performing action: {action_type} on {target}")
            
            # Wait before performing the action if needed
            time.sleep(Config.ACTION_DELAY)
            
            if action_type == 'CLICK':
                return self._handle_click(target)
                
            elif action_type == 'INPUT':
                return self._handle_input(target, value)
                
            elif action_type == 'SCROLL':
                return self._handle_scroll(target)
                
            elif action_type == 'WAIT':
                time.sleep(float(value) if value else Config.ACTION_DELAY)
                return True, STATUS_CODES['SUCCESS']
                
            else:
                return False, STATUS_CODES['INVALID_INPUT']

        except Exception as e:
            self.logger.error(f"Action failed: {str(e)}")
            return False, STATUS_CODES['ERROR']

    def _handle_click(self, target: str) -> Tuple[bool, str]:
        """Handle a click action using Playwright"""
        try:
            # Playwright uses locator to handle elements
            element = self.page.locator(target)

            # Scroll into view and click
            element.scroll_into_view_if_needed()
            time.sleep(0.5)
            element.click()

            return True, STATUS_CODES['SUCCESS']
        except Exception as e:
            self.logger.error(f"Failed to click element {target}: {str(e)}")
            return False, STATUS_CODES['ERROR']

    def _handle_input(self, target: str, value: str) -> Tuple[bool, str]:
        """Handle an input action using Playwright"""
        try:
            element = self.page.locator(target)

            # Clear and type new value
            element.fill("")  # Clears the input
            element.fill(value)

            # Verification step if needed
            actual_value = element.input_value()
            if actual_value != value:
                return False, STATUS_CODES['ERROR']
                
            return True, STATUS_CODES['SUCCESS']
        
        except Exception as e:
            self.logger.error(f"Failed to input value {value} into element {target}: {str(e)}")
            return False, STATUS_CODES['ERROR']

    def _handle_scroll(self, target: str) -> Tuple[bool, str]:
        """Handle a scroll action using Playwright"""
        try:
            element = self.page.locator(target)
            element.scroll_into_view_if_needed()
            time.sleep(0.5)
            return True, STATUS_CODES['SUCCESS']
        except Exception as e:
            self.logger.error(f"Failed to scroll to element {target}: {str(e)}")
            return False, STATUS_CODES['ERROR']

    def take_screenshot(self, filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Maak een screenshot van de huidige pagina.
        
        Args:
            filename: Optionele filename, anders wordt default gebruikt
            
        Returns:
            Tuple[bool, str]: (success, message/filepath)
        """
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(Config.SCREENSHOT_DIR, f"snapshot_{timestamp}.png")

            # Zorg dat de directory bestaat
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Take a screenshot using Playwright
            self.page.screenshot(path=filename, full_page=True)

            # Resize for thumbnail (optional step)
            with Image.open(filename) as img:
                img.thumbnail(Config.SNAPSHOT_SIZE)
                thumb_filename = filename.replace('.png', '_thumb.png')
                img.save(thumb_filename)
            
            return True, thumb_filename
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {str(e)}")
            return False, STATUS_CODES['ERROR']
        
    async def cleanup(self):
        """Cleanup Playwright resources."""
        try:
            if self.browser:
                await self.browser.close()  # Close the browser context properly
                self.logger.info("Playwright browser closed successfully")

            if self.playwright:
                await self.playwright.stop()  # Correctly stop Playwright without using async exit context
                self.logger.info("Playwright instance stopped successfully")

        except Exception as e:
            self.logger.error(f"Failed to clean up Playwright resources: {str(e)}")

    def __del__(self):
        """Destructor for cleanup"""
        self.cleanup()
        
# Example usage
if __name__ == "__main__":
    handler = WebPageHandler()
    success = handler.load_page("https://www.google.com")
    if success:
        handler.get_snapshot("snapshot.png")
    handler.cleanup()