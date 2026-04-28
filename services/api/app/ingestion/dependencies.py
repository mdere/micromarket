from app.ingestion.url_provider import TrafilaturaURLExtractionProvider, URLExtractionProvider


def get_url_extraction_provider() -> URLExtractionProvider:
    return TrafilaturaURLExtractionProvider()
