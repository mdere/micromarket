import httpx

from app.ingestion.url_provider import TrafilaturaURLExtractionProvider, URLExtractionError


def test_url_provider_reports_blocked_publisher(monkeypatch) -> None:
    provider = TrafilaturaURLExtractionProvider()
    request = httpx.Request("GET", "https://www.barrons.com/articles/stock-movers-2dd746cc")
    response = httpx.Response(401, request=request)

    def fake_get(*args, **kwargs) -> httpx.Response:
        return response

    monkeypatch.setattr(httpx, "get", fake_get)

    try:
        provider.extract("https://www.barrons.com/articles/stock-movers-2dd746cc")
    except URLExtractionError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected URLExtractionError.")

    assert "publisher blocked automated extraction" in message
    assert "HTTP 401" in message
    assert "Paste the article text manually" in message
