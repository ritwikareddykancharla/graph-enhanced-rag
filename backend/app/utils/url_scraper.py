"""URL scraping utility"""

import re
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


async def scrape_url(url: str, timeout: int = 30) -> str:
    """
    Scrape and extract text content from a URL.

    Args:
        url: URL to scrape
        timeout: Request timeout in seconds

    Returns:
        Extracted text content

    Raises:
        ValueError: If URL is invalid or scraping fails
    """
    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    # Fetch the page
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GraphRAG/1.0; +https://github.com/ritwikareddykancharla/graph-enhanced-rag)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"HTTP error {e.response.status_code} while fetching {url}"
            )
        except httpx.RequestError as e:
            raise ValueError(f"Failed to fetch {url}: {str(e)}")

    # Check content type
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise ValueError(f"Unsupported content type: {content_type}")

    # Parse HTML
    if "text/html" in content_type:
        return _extract_text_from_html(response.text, url)
    else:
        # Plain text
        return response.text


def _extract_text_from_html(html: str, url: str) -> str:
    """
    Extract readable text from HTML content.

    Args:
        html: HTML content
        url: Source URL (for context)

    Returns:
        Extracted text
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove unwanted elements
    for element in soup(
        ["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]
    ):
        element.decompose()

    # Try to find main content area
    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"content|main|article|post|entry", re.I))
        or soup.find("div", id=re.compile(r"content|main|article|post|entry", re.I))
        or soup.body
    )

    if not main_content:
        main_content = soup

    # Extract text
    text = main_content.get_text(separator="\n", strip=True)

    # Clean up text
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        # Skip empty lines and very short lines (likely noise)
        if len(line) < 3:
            continue
        # Skip lines that look like navigation or boilerplate
        if _is_boilerplate(line):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def _is_boilerplate(line: str) -> bool:
    """
    Check if a line is likely boilerplate/navigation text.

    Args:
        line: Line to check

    Returns:
        True if likely boilerplate
    """
    line_lower = line.lower()

    # Common boilerplate patterns
    boilerplate_patterns = [
        r"^skip to",
        r"^jump to",
        r"^click here",
        r"^read more",
        r"^share this",
        r"^follow us",
        r"^subscribe",
        r"^cookie",
        r"^privacy policy",
        r"^terms of",
        r"^sign in",
        r"^log in",
        r"^sign up",
        r"^register",
        r"^© \d{4}",
        r"^all rights reserved",
        r"^copyright",
    ]

    for pattern in boilerplate_patterns:
        if re.match(pattern, line_lower):
            return True

    # Check if line is mostly links (not useful for extraction)
    if line.count("http") > 3:
        return True

    return False


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract page title.

    Args:
        soup: BeautifulSoup object

    Returns:
        Page title or None
    """
    # Try og:title first
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"]

    # Try h1
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    # Try title tag
    title = soup.find("title")
    if title:
        return title.get_text(strip=True)

    return None
