#!/usr/bin/env python3
"""
Sherlock Content Ingestion - Normalize diverse content to UTF-8 text
Converts sources (files, URLs) to standardized .txt format for processing
"""

import os
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def ingest(path_or_url: str, output_dir: Optional[str] = None) -> str:
    """
    Ingest content from path or URL and normalize to UTF-8 text

    Args:
        path_or_url: Local file path or URL
        output_dir: Output directory for normalized text (default: ops/processed)

    Returns:
        Path to normalized .txt file

    Raises:
        ValueError: If source type not supported
        FileNotFoundError: If local file doesn't exist
    """
    # Determine if path or URL
    parsed = urlparse(path_or_url)
    is_url = bool(parsed.scheme and parsed.netloc)

    if is_url:
        return _ingest_url(path_or_url, output_dir)
    else:
        return _ingest_file(path_or_url, output_dir)


def _ingest_file(file_path: str, output_dir: Optional[str] = None) -> str:
    """Ingest local file and convert to UTF-8 text"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Default output dir
    if output_dir is None:
        output_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/processed"
    os.makedirs(output_dir, exist_ok=True)

    # Determine file type and convert
    suffix = path.suffix.lower()

    if suffix == '.txt':
        return _ingest_txt(path, output_dir)
    elif suffix == '.md':
        return _ingest_markdown(path, output_dir)
    elif suffix == '.pdf':
        return _ingest_pdf(path, output_dir)
    elif suffix in ['.html', '.htm']:
        return _ingest_html(path, output_dir)
    elif suffix == '.json':
        return _ingest_json(path, output_dir)
    else:
        # Try as plain text
        logger.warning(f"Unknown file type {suffix}, attempting plain text read")
        return _ingest_txt(path, output_dir)


def _ingest_txt(path: Path, output_dir: str) -> str:
    """Ingest plain text file"""
    # Read with multiple encoding attempts
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not decode {path} with any supported encoding")

    # Write normalized UTF-8
    output_path = os.path.join(output_dir, f"{path.stem}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Ingested {path} → {output_path} ({len(content)} chars)")
    return output_path


def _ingest_markdown(path: Path, output_dir: str) -> str:
    """Ingest Markdown file (treat as plain text for now)"""
    return _ingest_txt(path, output_dir)


def _ingest_pdf(path: Path, output_dir: str) -> str:
    """Ingest PDF file"""
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber not installed - cannot process PDF files")
        raise ValueError("PDF processing requires: pip install pdfplumber")

    # Extract text from PDF
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

    content = "\n\n".join(text_parts)

    # Write normalized UTF-8
    output_path = os.path.join(output_dir, f"{path.stem}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Ingested PDF {path} → {output_path} ({len(content)} chars)")
    return output_path


def _ingest_html(path: Path, output_dir: str) -> str:
    """Ingest HTML file"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 not installed - cannot process HTML files")
        raise ValueError("HTML processing requires: pip install beautifulsoup4")

    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Parse and extract text
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text
    content = soup.get_text(separator='\n', strip=True)

    # Write normalized UTF-8
    output_path = os.path.join(output_dir, f"{path.stem}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Ingested HTML {path} → {output_path} ({len(content)} chars)")
    return output_path


def _ingest_json(path: Path, output_dir: str) -> str:
    """Ingest JSON file (extract text fields)"""
    import json

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract text from common fields
    text_parts = []

    def extract_text(obj, depth=0):
        """Recursively extract text from JSON"""
        if depth > 10:  # Prevent infinite recursion
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and len(value) > 10:
                    text_parts.append(f"{key}: {value}")
                else:
                    extract_text(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                extract_text(item, depth + 1)
        elif isinstance(obj, str):
            text_parts.append(obj)

    extract_text(data)
    content = "\n\n".join(text_parts)

    # Write normalized UTF-8
    output_path = os.path.join(output_dir, f"{path.stem}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Ingested JSON {path} → {output_path} ({len(content)} chars)")
    return output_path


def _ingest_url(url: str, output_dir: Optional[str] = None) -> str:
    """Ingest content from URL"""
    try:
        from bs4 import BeautifulSoup
        import requests
    except ImportError:
        logger.error("beautifulsoup4 and requests required for URL ingestion")
        raise ValueError("URL processing requires: pip install beautifulsoup4 requests")

    # Default output dir
    if output_dir is None:
        output_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/processed"
    os.makedirs(output_dir, exist_ok=True)

    # Fetch URL
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text
    content = soup.get_text(separator='\n', strip=True)

    # Generate filename from URL
    parsed = urlparse(url)
    filename = parsed.path.strip('/').replace('/', '_') or 'index'
    if not filename.endswith('.txt'):
        filename += '.txt'

    # Write normalized UTF-8
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Ingested URL {url} → {output_path} ({len(content)} chars)")
    return output_path


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with sample text file
    test_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/inbox"
    os.makedirs(test_dir, exist_ok=True)

    # Create test file
    test_file = os.path.join(test_dir, "test_input.txt")
    with open(test_file, 'w') as f:
        f.write("This is a test document.\n\nIt has multiple paragraphs.\n\nFor testing ingestion.")

    # Test ingestion
    output_path = ingest(test_file)
    print(f"Ingested to: {output_path}")

    # Read result
    with open(output_path, 'r') as f:
        print("\nContent:")
        print(f.read())
