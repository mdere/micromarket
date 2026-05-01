from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

import httpx


class URLExtractionError(RuntimeError):
    pass


@dataclass(frozen=True)
class URLExtractionResult:
    url: str
    final_url: str
    title: str | None
    source: str | None
    text: str
    raw_html: str


class URLExtractionProvider(Protocol):
    def extract(self, url: str) -> URLExtractionResult:
        """Fetch a URL and extract readable article text."""


class TrafilaturaURLExtractionProvider:
    user_agent = "micromarket/0.1 local research article extraction"

    def extract(self, url: str) -> URLExtractionResult:
        normalized_url = self._normalize_url(url)
        try:
            response = httpx.get(
                normalized_url,
                follow_redirects=True,
                timeout=15,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise URLExtractionError(_fetch_error_message(normalized_url, exc.response)) from exc
        except httpx.HTTPError as exc:
            raise URLExtractionError(f"Could not fetch article URL {normalized_url}: {exc}") from exc

        raw_html = response.text
        extracted_text, title, source = self._extract_text(raw_html, str(response.url))
        if not extracted_text.strip():
            raise URLExtractionError(f"No article text could be extracted from {normalized_url}.")

        return URLExtractionResult(
            url=normalized_url,
            final_url=str(response.url),
            title=title,
            source=source,
            text=extracted_text,
            raw_html=raw_html,
        )

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise URLExtractionError("Article URL must be an absolute http(s) URL.")
        return url.strip()

    def _extract_text(self, html: str, url: str) -> tuple[str, str | None, str | None]:
        try:
            import trafilatura
        except ImportError as exc:
            raise URLExtractionError(
                "URL extraction requires the trafilatura package. "
                'Install backend dependencies with python -m pip install -e ".[dev]".'
            ) from exc

        text = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            output_format="txt",
        )
        metadata = trafilatura.extract_metadata(html, default_url=url)
        title = getattr(metadata, "title", None) if metadata is not None else None
        source = getattr(metadata, "sitename", None) if metadata is not None else None
        return text or "", title, source


def _fetch_error_message(url: str, response: httpx.Response) -> str:
    status_code = response.status_code
    if status_code in {401, 403}:
        return (
            f"Could not fetch article URL {url}: the publisher blocked automated extraction "
            f"with HTTP {status_code}. Paste the article text manually to continue, or use a "
            "freely accessible source URL."
        )
    return f"Could not fetch article URL {url}: HTTP {status_code} {response.reason_phrase}."
