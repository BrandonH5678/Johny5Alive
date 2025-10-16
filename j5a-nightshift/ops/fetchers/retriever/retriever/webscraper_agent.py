"""
WebScraperAgent - Advanced web scraping with Selenium/Playwright
"""
from __future__ import annotations
import logging
import time as time_module
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseAgent

logger = logging.getLogger(__name__)


class WebScraperAgent(BaseAgent):
    """
    Scrapes web content using Selenium or Playwright

    Supports:
    - JavaScript-heavy sites
    - Dynamic content loading
    - Element selection (CSS, XPath)
    - Screenshots
    - Form interaction
    - Headless/headful mode
    - Multiple browsers (Chrome, Firefox, Safari)
    """

    def __init__(
        self,
        backend: str = 'selenium',
        browser: str = 'chrome',
        headless: bool = True,
        timeout: int = 30,
        screenshot_dir: Optional[str] = None
    ):
        """
        Initialize WebScraperAgent

        Args:
            backend: Scraping backend ('selenium' or 'playwright')
            browser: Browser to use ('chrome', 'firefox', 'safari')
            headless: Run browser in headless mode
            timeout: Page load timeout in seconds
            screenshot_dir: Directory to save screenshots
        """
        self.backend = backend.lower()
        self.browser = browser.lower()
        self.headless = headless
        self.timeout = timeout
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else None

        if self.screenshot_dir:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"WebScraperAgent initialized with {backend} backend ({browser})")

    def supports(self, target: Any) -> bool:
        """Check if target is a web scraping operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('webscraper', 'scrape', 'selenium', 'playwright')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Scrape web content

        Target structure:
            {
                'type': 'webscraper',
                'url': 'https://example.com',
                'backend': 'selenium' | 'playwright' (optional),
                'wait_for': 'css_selector' (optional, wait for element),
                'wait_time': 5 (optional, wait N seconds),
                'selectors': {
                    'title': 'h1.title',
                    'items': '.item-list .item',
                    'price': '.price'
                },
                'extract': 'text' | 'html' | 'attribute' (default 'text'),
                'attribute': 'href' (for extract='attribute'),
                'screenshot': True (optional, take screenshot),
                'screenshot_name': 'page.png' (optional),
                'actions': [  # Optional, perform actions before scraping
                    {'type': 'click', 'selector': 'button.submit'},
                    {'type': 'fill', 'selector': 'input[name="q"]', 'value': 'search query'},
                    {'type': 'wait', 'seconds': 2}
                ]
            }

        Returns:
            {
                'data': {
                    'title': 'Page Title',
                    'items': ['Item 1', 'Item 2', ...],
                    'price': '$19.99'
                },
                'url': 'https://example.com',
                'screenshot_path': '/path/to/screenshot.png' (if requested),
                'meta': {
                    'method': 'webscraper',
                    'backend': 'selenium',
                    'browser': 'chrome',
                    'scrape_time_ms': 1234
                }
            }
        """
        import time

        start_time = time.time()

        url = target.get('url')
        if not url:
            raise ValueError("URL required")

        backend = target.get('backend', self.backend)

        logger.info(f"Scraping {url} with {backend}")

        if backend == 'selenium':
            result = self._scrape_selenium(target)
        elif backend == 'playwright':
            result = self._scrape_playwright(target)
        else:
            raise ValueError(f"Unknown backend: {backend}")

        scrape_time_ms = int((time.time() - start_time) * 1000)

        result['meta'] = {
            'method': 'webscraper',
            'backend': backend,
            'browser': self.browser,
            'scrape_time_ms': scrape_time_ms
        }

        return result

    def _scrape_selenium(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape using Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except ImportError:
            raise ImportError("Selenium not installed - install with: pip install selenium")

        url = target['url']

        # Setup browser options
        if self.browser == 'chrome':
            from selenium.webdriver.chrome.options import Options
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)
        elif self.browser == 'firefox':
            from selenium.webdriver.firefox.options import Options
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

        try:
            driver.set_page_load_timeout(self.timeout)

            # Load page
            driver.get(url)

            # Wait for specific element if specified
            if 'wait_for' in target:
                wait = WebDriverWait(driver, self.timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, target['wait_for'])))

            # Additional wait time
            if 'wait_time' in target:
                time_module.sleep(target['wait_time'])

            # Perform actions if specified
            if 'actions' in target:
                self._perform_actions_selenium(driver, target['actions'])

            # Extract data using selectors
            selectors = target.get('selectors', {})
            extract_mode = target.get('extract', 'text')
            attribute = target.get('attribute', 'href')

            data = {}
            for key, selector in selectors.items():
                data[key] = self._extract_selenium(
                    driver, selector, extract_mode, attribute
                )

            # Take screenshot if requested
            screenshot_path = None
            if target.get('screenshot'):
                screenshot_name = target.get('screenshot_name', 'screenshot.png')
                if self.screenshot_dir:
                    screenshot_path = self.screenshot_dir / screenshot_name
                else:
                    screenshot_path = Path(screenshot_name)

                driver.save_screenshot(str(screenshot_path))
                logger.info(f"Screenshot saved to {screenshot_path}")

            return {
                'data': data,
                'url': driver.current_url,
                'screenshot_path': str(screenshot_path) if screenshot_path else None
            }

        finally:
            driver.quit()

    def _perform_actions_selenium(self, driver, actions: List[Dict[str, Any]]):
        """Perform actions on page with Selenium"""
        from selenium.webdriver.common.by import By

        for action in actions:
            action_type = action.get('type')

            if action_type == 'click':
                element = driver.find_element(By.CSS_SELECTOR, action['selector'])
                element.click()

            elif action_type == 'fill':
                element = driver.find_element(By.CSS_SELECTOR, action['selector'])
                element.clear()
                element.send_keys(action['value'])

            elif action_type == 'wait':
                time_module.sleep(action.get('seconds', 1))

    def _extract_selenium(
        self,
        driver,
        selector: str,
        extract_mode: str,
        attribute: str
    ) -> Any:
        """Extract data from elements with Selenium"""
        from selenium.webdriver.common.by import By

        elements = driver.find_elements(By.CSS_SELECTOR, selector)

        if not elements:
            return None

        # Single element
        if len(elements) == 1:
            element = elements[0]

            if extract_mode == 'text':
                return element.text
            elif extract_mode == 'html':
                return element.get_attribute('innerHTML')
            elif extract_mode == 'attribute':
                return element.get_attribute(attribute)

        # Multiple elements
        results = []
        for element in elements:
            if extract_mode == 'text':
                results.append(element.text)
            elif extract_mode == 'html':
                results.append(element.get_attribute('innerHTML'))
            elif extract_mode == 'attribute':
                results.append(element.get_attribute(attribute))

        return results

    def _scrape_playwright(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape using Playwright"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError("Playwright not installed - install with: pip install playwright && playwright install")

        url = target['url']

        with sync_playwright() as p:
            # Launch browser
            if self.browser == 'chrome' or self.browser == 'chromium':
                browser = p.chromium.launch(headless=self.headless)
            elif self.browser == 'firefox':
                browser = p.firefox.launch(headless=self.headless)
            elif self.browser == 'safari' or self.browser == 'webkit':
                browser = p.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")

            try:
                page = browser.new_page()
                page.set_default_timeout(self.timeout * 1000)

                # Navigate to URL
                page.goto(url)

                # Wait for specific element if specified
                if 'wait_for' in target:
                    page.wait_for_selector(target['wait_for'])

                # Additional wait time
                if 'wait_time' in target:
                    time_module.sleep(target['wait_time'])

                # Perform actions if specified
                if 'actions' in target:
                    self._perform_actions_playwright(page, target['actions'])

                # Extract data using selectors
                selectors = target.get('selectors', {})
                extract_mode = target.get('extract', 'text')
                attribute = target.get('attribute', 'href')

                data = {}
                for key, selector in selectors.items():
                    data[key] = self._extract_playwright(
                        page, selector, extract_mode, attribute
                    )

                # Take screenshot if requested
                screenshot_path = None
                if target.get('screenshot'):
                    screenshot_name = target.get('screenshot_name', 'screenshot.png')
                    if self.screenshot_dir:
                        screenshot_path = self.screenshot_dir / screenshot_name
                    else:
                        screenshot_path = Path(screenshot_name)

                    page.screenshot(path=str(screenshot_path))
                    logger.info(f"Screenshot saved to {screenshot_path}")

                return {
                    'data': data,
                    'url': page.url,
                    'screenshot_path': str(screenshot_path) if screenshot_path else None
                }

            finally:
                browser.close()

    def _perform_actions_playwright(self, page, actions: List[Dict[str, Any]]):
        """Perform actions on page with Playwright"""
        for action in actions:
            action_type = action.get('type')

            if action_type == 'click':
                page.click(action['selector'])

            elif action_type == 'fill':
                page.fill(action['selector'], action['value'])

            elif action_type == 'wait':
                time_module.sleep(action.get('seconds', 1))

    def _extract_playwright(
        self,
        page,
        selector: str,
        extract_mode: str,
        attribute: str
    ) -> Any:
        """Extract data from elements with Playwright"""
        elements = page.query_selector_all(selector)

        if not elements:
            return None

        # Single element
        if len(elements) == 1:
            element = elements[0]

            if extract_mode == 'text':
                return element.text_content()
            elif extract_mode == 'html':
                return element.inner_html()
            elif extract_mode == 'attribute':
                return element.get_attribute(attribute)

        # Multiple elements
        results = []
        for element in elements:
            if extract_mode == 'text':
                results.append(element.text_content())
            elif extract_mode == 'html':
                results.append(element.inner_html())
            elif extract_mode == 'attribute':
                results.append(element.get_attribute(attribute))

        return results
