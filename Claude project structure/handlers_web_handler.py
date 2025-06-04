"""
Web Handler Module

Beheert alle web-gerelateerde interacties via Selenium WebDriver.
"""

import os
import time
import json
import logging
from typing import Optional, Tuple, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

from ..config import Config
from ..utils.constants import STATUS_CODES  # Direct import van constants

class WebPageHandler:
    """Handler voor web interacties via Selenium"""
    
    def __init__(self):
        """Initialiseer de WebPageHandler met Selenium WebDriver"""
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self) -> None:
        """
        Initialiseer de Chrome WebDriver met de juiste opties.
        
        Raises:
            WebDriverException: Als driver setup faalt
        """
        try:
            chrome_options = Options()
            for option in Config.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Set timeouts
            self.driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(Config.ELEMENT_TIMEOUT)
            
            self.logger.info("WebDriver successfully initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise WebDriverException(f"Driver setup failed: {str(e)}")

    def load_page(self, url: str) -> Tuple[bool, str]:
        """
        Laad een webpagina en wacht tot deze volledig geladen is.
        
        Args:
            url: De URL om te laden
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.logger.info(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wacht tot pagina geladen is
            WebDriverWait(self.driver, Config.PAGE_LOAD_TIMEOUT).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            self.logger.info("Page loaded successfully")
            return True, STATUS_CODES['SUCCESS']
            
        except TimeoutException:
            msg = "Page load timed out"
            self.logger.error(msg)
            return False, STATUS_CODES['TIMEOUT']
            
        except WebDriverException as e:
            msg = str(e)
            if "net::ERR_NAME_NOT_RESOLVED" in msg:
                return False, STATUS_CODES['NOT_FOUND']
            elif "net::ERR_CONNECTION_TIMED_OUT" in msg:
                return False, STATUS_CODES['TIMEOUT']
            elif "net::ERR_CONNECTION_REFUSED" in msg:
                return False, STATUS_CODES['SERVER_ERROR']
                
            self.logger.error(f"Failed to load page: {msg}")
            return False, STATUS_CODES['ERROR']

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Maak een snapshot van de huidige pagina status.
        
        Returns:
            Dictionary met pagina informatie
        """
        try:
            snapshot = {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "html_preview": self.driver.page_source[:500],
                "elements": []
            }

            # Verzamel alle interactieve elementen
            elements = self.driver.find_elements(
                By.XPATH,
                "//button | //input | //a | //select | //textarea | //iframe"
            )
            
            for element in elements:
                try:
                    element_info = {
                        "tag": element.tag_name,
                        "text": element.text.strip(),
                        "xpath": self.get_element_xpath(element),
                        "attributes": {
                            "id": element.get_attribute("id"),
                            "class": element.get_attribute("class"),
                            "name": element.get_attribute("name"),
                            "type": element.get_attribute("type"),
                            "value": element.get_attribute("value"),
                            "placeholder": element.get_attribute("placeholder")
                        },
                        "is_visible": element.is_displayed(),
                        "is_enabled": element.is_enabled()
                    }
                    snapshot["elements"].append(element_info)
                except StaleElementReferenceException:
                    continue
                    
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to get snapshot: {str(e)}")
            return {"error": str(e)}

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
            
            # Wacht kort voor de actie
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
        """Handle een click actie"""
        try:
            element = WebDriverWait(self.driver, Config.ELEMENT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, target))
            )
            
            # Scroll element into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(0.5)
            
            # Probeer te clicken
            element.click()
            return True, STATUS_CODES['SUCCESS']
            
        except ElementClickInterceptedException:
            # Probeer JavaScript click als normale click faalt
            try:
                element = self.driver.find_element(By.XPATH, target)
                self.driver.execute_script("arguments[0].click();", element)
                return True, f"{STATUS_CODES['SUCCESS']} (via JavaScript)"
            except Exception as e:
                return False, STATUS_CODES['ERROR']
                
        except Exception as e:
            return False, STATUS_CODES['ERROR']

    def _handle_input(self, target: str, value: str) -> Tuple[bool, str]:
        """Handle een input actie"""
        try:
            element = WebDriverWait(self.driver, Config.ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, target))
            )
            
            # Clear huidige waarde
            element.clear()
            
            # Type nieuwe waarde
            element.send_keys(value)
            
            # Check of waarde correct is ingevuld
            actual_value = element.get_attribute('value')
            if actual_value != value:
                return False, STATUS_CODES['ERROR']
                
            return True, STATUS_CODES['SUCCESS']
            
        except Exception as e:
            return False, STATUS_CODES['ERROR']

    def _handle_scroll(self, target: str) -> Tuple[bool, str]:
        """Handle een scroll actie"""
        try:
            element = self.driver.find_element(By.XPATH, target)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(0.5)
            return True, STATUS_CODES['SUCCESS']
            
        except Exception as e:
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

            # Neem screenshot
            self.driver.save_screenshot(filename)
            
            # Resize voor thumbnail
            with Image.open(filename) as img:
                img.thumbnail(Config.SNAPSHOT_SIZE)
                thumb_filename = filename.replace('.png', '_thumb.png')
                img.save(thumb_filename)
            
            return True, thumb_filename
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {str(e)}")
            return False, STATUS_CODES['ERROR']

    @staticmethod
    def get_element_xpath(element: webdriver.remote.webelement.WebElement) -> str:
        """Genereer een XPath voor een element"""
        components = []
        child = element
        
        while child:
            parent = child.find_element(By.XPATH, "..")
            siblings = parent.find_elements(By.XPATH, f"./{child.tag_name}")
            
            if len(siblings) > 1:
                index = siblings.index(child) + 1
                components.append(f"{child.tag_name}[{index}]")
            else:
                components.append(child.tag_name)
                
            child = parent if parent.tag_name != "html" else None
            
        components.reverse()
        return "/" + "/".join(components)

    def cleanup(self) -> None:
        """Cleanup WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver cleanup successful")
            except Exception as e:
                self.logger.error(f"WebDriver cleanup failed: {str(e)}")

    def __del__(self):
        """Destructor voor cleanup"""
        self.cleanup()