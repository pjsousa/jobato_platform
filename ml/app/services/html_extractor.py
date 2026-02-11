from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser


_WHITESPACE = re.compile(r"\s+")
_EXCLUDED_TAGS = {"script", "style", "noscript", "meta", "link", "title"}


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._excluded_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in _EXCLUDED_TAGS:
            self._excluded_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _EXCLUDED_TAGS and self._excluded_depth > 0:
            self._excluded_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._excluded_depth == 0 and data:
            self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._excluded_depth == 0:
            self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._excluded_depth == 0:
            self._parts.append(f"&#{name};")

    @property
    def text(self) -> str:
        return "".join(self._parts)


class HtmlExtractor:
    def extract_visible_text(self, html_content: str) -> tuple[str, str | None]:
        try:
            parser = _VisibleTextParser()
            parser.feed(html_content or "")
            parser.close()

            text = unescape(parser.text)
            text = _WHITESPACE.sub(" ", text).strip()
            return text, None
        except Exception as error:
            return "", str(error)
