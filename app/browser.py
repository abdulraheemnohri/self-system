#!/usr/bin/env python3
"""
Browser Automation Module for the Complete Self System

Provides:
- Headless browser control via Playwright
- Page navigation
- Form filling
- Click actions
- Text extraction
- Screenshot capture
"""

import os
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path


class BrowserManager:
    """
    Browser automation using Playwright.
    
    Supports:
    - Chromium (default)
    - Firefox
    - WebKit
    
    Features:
    - Page navigation
    - Form interaction
    - Text extraction
    - Screenshot capture
    - PDF generation
    """
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        """
        Initialize the BrowserManager.
        
        Args:
            headless: Run browser in headless mode
            browser_type: Type of browser (chromium, firefox, webkit)
        """
        self.headless = headless
        self.browser_type = browser_type
        self.installed = False
        self.p = None
        self.browser = None
        self.page = None
        self.context = None
        self.sync_playwright = None
        self._ensure_playwright()
    
    def _ensure_playwright(self) -> None:
        """Ensure Playwright is installed."""
        try:
            from playwright.sync_api import sync_playwright
            self.sync_playwright = sync_playwright
            self.installed = True
        except ImportError:
            self.installed = False
    
    def _ensure_browser(self) -> Optional[str]:
        """
        Ensure browser is launched and ready.
        
        Returns:
            Error message if browser cannot be launched, None otherwise
        """
        if not self.installed:
            return "Browser automation unavailable. Install with: pip install playwright && python -m playwright install"
        
        if not self.browser:
            try:
                self.p = self.sync_playwright().start()
                
                if self.browser_type == "chromium":
                    self.browser = self.p.chromium.launch(headless=self.headless)
                elif self.browser_type == "firefox":
                    self.browser = self.p.firefox.launch(headless=self.headless)
                elif self.browser_type == "webkit":
                    self.browser = self.p.webkit.launch(headless=self.headless)
                else:
                    self.browser = self.p.chromium.launch(headless=self.headless)
                
                self.context = self.browser.new_context()
                self.page = self.context.new_page()
                
                # Set default timeout
                self.page.set_default_timeout(30000)
                
            except Exception as e:
                return f"Failed to launch browser: {str(e)}"
        
        return None
    
    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: Wait condition (load, domcontentloaded, networkidle)
            
        Returns:
            Dictionary with page info (title, url, status)
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            self.page.goto(url, wait_until=wait_until)
            
            return {
                "success": True,
                "title": self.page.title(),
                "url": self.page.url,
                "status": "loaded"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def fill(self, selector: str, text: str, delay: int = 50) -> Dict[str, Any]:
        """
        Fill a form field using CSS selector.
        
        Args:
            selector: CSS selector for the input field
            text: Text to fill
            delay: Delay between keystrokes in ms
            
        Returns:
            Dictionary with success status
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.fill(selector, text, delay=delay)
            return {"success": True, "message": f"Filled selector '{selector}'"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def click(self, selector: str, button: str = "left", delay: int = 100) -> Dict[str, Any]:
        """
        Click an element using CSS selector.
        
        Args:
            selector: CSS selector for the element to click
            button: Mouse button (left, right, middle)
            delay: Delay after click in ms
            
        Returns:
            Dictionary with success status
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.click(selector, button=button, delay=delay)
            return {"success": True, "message": f"Clicked selector '{selector}'"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def type_text(self, selector: str, text: str, delay: int = 50) -> Dict[str, Any]:
        """
        Type text into an element (simulates keyboard input).
        
        Args:
            selector: CSS selector for the element
            text: Text to type
            delay: Delay between keystrokes in ms
            
        Returns:
            Dictionary with success status
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.type(selector, text, delay=delay)
            return {"success": True, "message": f"Typed text into selector '{selector}'"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def press_key(self, key: str) -> Dict[str, Any]:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (Enter, Tab, Escape, etc.)
            
        Returns:
            Dictionary with success status
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.keyboard.press(key)
            return {"success": True, "message": f"Pressed key '{key}'"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_text(self, selector: str = "body") -> Dict[str, Any]:
        """
        Extract text from an element.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            Dictionary with extracted text
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "text": "", "success": False}
        
        try:
            text = self.page.inner_text(selector)
            return {"success": True, "text": text, "selector": selector}
        except Exception as e:
            return {"error": str(e), "text": "", "success": False}
    
    def get_content(self) -> Dict[str, Any]:
        """
        Get the full page content.
        
        Returns:
            Dictionary with page content
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "content": "", "success": False}
        
        try:
            content = self.page.content()
            return {"success": True, "content": content}
        except Exception as e:
            return {"error": str(e), "content": "", "success": False}
    
    def take_screenshot(self, path: str = "screenshot.png", full_page: bool = False) -> Dict[str, Any]:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Path to save the screenshot
            full_page: Capture full scrollable page
            
        Returns:
            Dictionary with screenshot path and success status
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            self.page.screenshot(path=path, full_page=full_page)
            return {"success": True, "path": path, "message": "Screenshot saved"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def generate_pdf(self, path: str = "page.pdf") -> Dict[str, Any]:
        """
        Generate a PDF of the current page.
        
        Args:
            path: Path to save the PDF
            
        Returns:
            Dictionary with PDF path and success status
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.page.pdf(path=path)
            return {"success": True, "path": path, "message": "PDF generated"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def go_back(self) -> Dict[str, Any]:
        """Navigate back in browser history."""
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.go_back()
            return {"success": True, "message": "Navigated back"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def go_forward(self) -> Dict[str, Any]:
        """Navigate forward in browser history."""
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.go_forward()
            return {"success": True, "message": "Navigated forward"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def reload(self) -> Dict[str, Any]:
        """Reload the current page."""
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.reload()
            return {"success": True, "message": "Page reloaded"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def wait_for_selector(self, selector: str, timeout: int = 5000, state: str = "visible") -> Dict[str, Any]:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds
            state: State to wait for (visible, hidden, attached, detached)
            
        Returns:
            Dictionary with success status
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state=state)
            return {"success": True, "message": f"Element '{selector}' found"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def evaluate(self, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript in the page context.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Dictionary with the result
        """
        err = self._ensure_browser()
        if err:
            return {"error": err, "success": False}
        
        try:
            result = self.page.evaluate(script)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_title(self) -> Dict[str, Any]:
        """Get the current page title."""
        err = self._ensure_browser()
        if err:
            return {"error": err, "title": "", "success": False}
        
        try:
            return {"success": True, "title": self.page.title()}
        except Exception as e:
            return {"error": str(e), "title": "", "success": False}
    
    def get_url(self) -> Dict[str, Any]:
        """Get the current page URL."""
        err = self._ensure_browser()
        if err:
            return {"error": err, "url": "", "success": False}
        
        try:
            return {"success": True, "url": self.page.url}
        except Exception as e:
            return {"error": str(e), "url": "", "success": False}
    
    def close(self) -> None:
        """Close the browser and cleanup."""
        if self.browser:
            try:
                self.context.close()
                self.browser.close()
                if self.p:
                    self.p.stop()
            except Exception:
                pass
            finally:
                self.page = None
                self.context = None
                self.browser = None
                self.p = None
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()


def create_browser_manager(headless: bool = True, browser_type: str = "chromium") -> BrowserManager:
    """
    Factory function to create a BrowserManager instance.
    
    Args:
        headless: Run browser in headless mode
        browser_type: Type of browser (chromium, firefox, webkit)
        
    Returns:
        BrowserManager instance
    """
    return BrowserManager(headless=headless, browser_type=browser_type)
