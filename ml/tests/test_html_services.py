import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.html_fetcher import HtmlFetcher
from app.services.html_extractor import HtmlExtractor


def test_html_fetcher_fetch_html_success():
    """Test successful HTML fetching and storage"""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        fetcher = HtmlFetcher(data_dir=tmp_dir)
        
        # Mock successful HTTP response
        with patch('app.services.html_fetcher.requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body><h1>Test</h1></body></html>"
            mock_get.return_value = mock_response
            
            # Test fetching
            file_path, error = fetcher.fetch_html("http://example.com")
            
            # Verify
            assert file_path is not None
            assert error is None
            assert Path(file_path).exists()
            assert "Test" in Path(file_path).read_text()


def test_html_fetcher_fetch_html_failure():
    """Test HTML fetching failure handling"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fetcher = HtmlFetcher(data_dir=tmp_dir)
        
        # Mock failed HTTP response
        with patch('app.services.html_fetcher.requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # Test fetching with error
            file_path, error = fetcher.fetch_html("http://example.com")
            
            # Verify
            assert file_path is None
            assert error is not None


def test_html_extractor_extract_visible_text():
    """Test HTML text extraction"""
    extractor = HtmlExtractor()
    
    # Test with typical HTML
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
    
    # Verify
    assert error is None
    assert "Main Heading" in extracted_text
    assert "Some bold text." in extracted_text
    assert "console.log" not in extracted_text
    assert "color: red" not in extracted_text


def test_html_extractor_extract_visible_text_empty():
    """Test HTML text extraction with empty content"""
    extractor = HtmlExtractor()
    
    extracted_text, error = extractor.extract_visible_text("")
    
    # Verify
    assert error is None
    assert extracted_text == ""


def test_html_extractor_extract_visible_text_malformed():
    """Test HTML text extraction with malformed HTML"""
    extractor = HtmlExtractor()
    
    # Test with malformed HTML
    malformed_html = "<html><body><p>Some content"
    
    extracted_text, error = extractor.extract_visible_text(malformed_html)
    
    # Should not crash, but return some text
    assert error is None
    assert "Some content" in extracted_text