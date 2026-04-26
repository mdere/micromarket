from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class NormalizedArticle:
    title: str | None
    source: str | None
    url: str | None
    text: str
    content_hash: str


class ArticleIngestionService:
    """Normalizes manual text and URL article inputs.

    URL fetching and extraction will be implemented after the first manual-text vertical slice.
    """

    def normalize_text(
        self, text: str, title: str | None = None, source: str | None = None
    ) -> NormalizedArticle:
        cleaned = " ".join(text.split())
        return NormalizedArticle(
            title=title,
            source=source or "manual",
            url=None,
            text=cleaned,
            content_hash=sha256(cleaned.encode("utf-8")).hexdigest(),
        )
