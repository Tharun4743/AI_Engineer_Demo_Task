from typing import Optional
from bs4 import BeautifulSoup

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False


class FullTextExtractor:
    """Extracts primary text content from HTML using trafilatura and BeautifulSoup fallbacks."""

    def extract_text(self, html_content: Optional[str]) -> str:
        if not html_content:
            return ""

        # Primary extraction: trafilatura
        if HAS_TRAFILATURA:
            try:
                extracted = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False
                )
                if extracted and len(extracted.strip()) > 50:
                    return extracted.strip()
            except Exception:
                pass

        # Secondary fallback: BeautifulSoup heuristic text extraction
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "aside"]):
                tag.decompose()

            # Prefer article, main, or content div
            target = soup.find("article") or soup.find("main") or soup.find("body") or soup
            text = target.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines)
        except Exception:
            return ""


fulltext_extractor = FullTextExtractor()
