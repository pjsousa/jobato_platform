import tempfile
from pathlib import Path
from unittest.mock import patch

from app.services.html_fetcher import HtmlFetcher
from app.services.html_extractor import HtmlExtractor


def test_html_fetcher_fetch_html_success():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fetcher = HtmlFetcher(data_dir=tmp_dir)

        file_path, error = fetcher.fetch_html("mock://example.com/jobs/abc", run_id="run-123")

        assert file_path is not None
        assert error is None
        assert Path(file_path).exists()
        assert "/html/raw/run-123/" in Path(file_path).as_posix()
        assert "Mock result for example.com" in Path(file_path).read_text(encoding="utf-8")

        repeated_path, repeated_error = fetcher.fetch_html("mock://example.com/jobs/abc", run_id="run-123")
        assert repeated_error is None
        assert repeated_path == file_path


def test_html_fetcher_fetch_html_failure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fetcher = HtmlFetcher(data_dir=tmp_dir)

        with patch("app.services.html_fetcher.urlopen", side_effect=TimeoutError("network timeout")):
            file_path, error = fetcher.fetch_html("https://example.com", run_id="run-123")

        assert file_path is None
        assert error is not None
        assert "network timeout" in error


def test_html_extractor_extract_visible_text():
    extractor = HtmlExtractor()

    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Main Heading</h1>
            <p>Some <strong>bold</strong> text.</p>
            <script>console.log('this should be removed');</script>
            <style>body { color: red; }</style>
        </body>
    </html>
    """

    extracted_text, error = extractor.extract_visible_text(html_content)

    assert error is None
    assert "Main Heading" in extracted_text
    assert "Some bold text." in extracted_text
    assert "console.log" not in extracted_text
    assert "color: red" not in extracted_text


def test_html_extractor_extract_visible_text_empty():
    extractor = HtmlExtractor()

    extracted_text, error = extractor.extract_visible_text("")

    assert error is None
    assert extracted_text == ""


def test_html_extractor_extract_visible_text_malformed():
    extractor = HtmlExtractor()

    malformed_html = "<html><body><p>Some content"

    extracted_text, error = extractor.extract_visible_text(malformed_html)

    assert error is None
    assert "Some content" in extracted_text


def test_html_extractor_decodes_entities_and_utf8_text():
    extractor = HtmlExtractor()

    extracted_text, error = extractor.extract_visible_text("<p>Caf&#233; &amp; r&#233;sum&#233;</p>")

    assert error is None
    assert "Caf" in extracted_text
    assert "&" in extracted_text
