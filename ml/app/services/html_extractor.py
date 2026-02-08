from __future__ import annotations

import re
from html import unescape
from typing import Optional

from bs4 import BeautifulSoup, NavigableString


class HtmlExtractor:
    def __init__(self):
        # Common script and style tags to remove
        self.script_style_tags = ["script", "style", "noscript", "meta", "link", "title"]
        
    def extract_visible_text(self, html_content: str) -> tuple[str, Optional[str]]:
        """
        Extract visible text from HTML content.
        
        Returns:
            tuple of (extracted_text, error_message) where:
            - extracted_text: visible text content or empty string if failed
            - error_message: error description or None if successful
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove unwanted tags
            for tag in soup(self.script_style_tags):
                tag.decompose()
                
            # Remove tags with specific attributes
            for tag in soup.find_all():
                # Remove attributes that might contain sensitive information
                for attr in list(tag.attrs.keys()):
                    if attr.startswith("on"):
                        del tag.attrs[attr]
            
            # Get text and clean it up
            text = soup.get_text()
            
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            # Handle HTML entities
            text = unescape(text)
            
            return text, None
            
        except Exception as e:
            return "", str(e)