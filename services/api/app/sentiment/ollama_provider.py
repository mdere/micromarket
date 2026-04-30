import json
import re
from dataclasses import replace
from typing import Any, Callable

import httpx

from app.sentiment.provider import SentimentProvider, SentimentProviderError, SentimentResult


OllamaPost = Callable[..., httpx.Response]


class OllamaSentimentProvider:
    provider_name = "ollama"
    model_name = "ollama-chat-sentiment"
    model_version = "0.1.0"
    valid_labels = {"positive", "neutral", "negative", "mixed"}

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434/api",
        model: str = "llama3.1:8b",
        timeout_seconds: float = 30.0,
        fallback_provider: SentimentProvider | None = None,
        post: OllamaPost | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.fallback_provider = fallback_provider
        self._post = post or httpx.post

    def score_article(self, article_text: str, ticker: str) -> SentimentResult:
        try:
            return self._score_article(article_text, ticker)
        except SentimentProviderError as exc:
            if self.fallback_provider is None:
                raise
            fallback = self.fallback_provider.score_article(article_text, ticker)
            return replace(
                fallback,
                limitations=[
                    *fallback.limitations,
                    f"Ollama sentiment provider failed; used fallback baseline. Error: {exc}",
                ],
            )

    def _score_article(self, article_text: str, ticker: str) -> SentimentResult:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You score financial article sentiment for research-only analysis. "
                        "Return only JSON. Do not provide investment advice or buy, sell, "
                        "or hold recommendations."
                    ),
                },
                {
                    "role": "user",
                    "content": self._user_prompt(article_text=article_text, ticker=ticker),
                },
            ],
            "format": "json",
        }
        try:
            response = self._post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SentimentProviderError(f"Ollama request failed: {exc}") from exc

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise SentimentProviderError("Ollama returned a non-JSON HTTP response.") from exc

        content = self._response_content(response_payload)
        raw_result = self._parse_model_json(content)
        return self._result_from_payload(raw_result)

    def _user_prompt(self, *, article_text: str, ticker: str) -> str:
        return (
            f"Ticker: {ticker.upper()}\n\n"
            "Analyze the article text for ticker-relevant financial sentiment. "
            "Use only the article evidence. Return a JSON object with exactly these keys: "
            "label, score, confidence, drivers, evidence_snippets, limitations. "
            "label must be one of positive, neutral, negative, mixed. "
            "score must be from -1.0 to 1.0. confidence must be from 0.0 to 1.0. "
            "drivers must be short categories such as earnings, guidance, demand, "
            "regulatory, valuation, macro, analyst_action, product, supply, or uncertainty. "
            "evidence_snippets must quote short article excerpts. limitations must include "
            "important caveats. Driver rules: include every materially relevant driver "
            "category supported by the article; for a mixed label, include drivers and "
            "evidence for both supportive and offsetting signals; do not include a driver "
            "unless it is supported by an evidence snippet; use uncertainty when the article "
            "uses may, could, unclear, limited conviction, cautious, or other confidence-limiting "
            "language; use analyst_action for upgrades, downgrades, or price target changes; "
            "use guidance for raised, lowered, cut, or warned guidance. Do not include "
            "investment advice.\n\n"
            f"Article text:\n{article_text[:12000]}"
        )

    def _response_content(self, response_payload: dict[str, Any]) -> str:
        message = response_payload.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
        if isinstance(response_payload.get("response"), str):
            return response_payload["response"]
        raise SentimentProviderError("Ollama response did not include model content.")

    def _parse_model_json(self, content: str) -> dict[str, Any]:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, flags=re.DOTALL)
            if match is None:
                raise SentimentProviderError("Ollama response content was not valid JSON.") from None
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise SentimentProviderError("Ollama response content was not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise SentimentProviderError("Ollama JSON response must be an object.")
        return parsed

    def _result_from_payload(self, payload: dict[str, Any]) -> SentimentResult:
        missing = {
            key
            for key in (
                "label",
                "score",
                "confidence",
                "drivers",
                "evidence_snippets",
                "limitations",
            )
            if key not in payload
        }
        if missing:
            raise SentimentProviderError(
                f"Ollama sentiment JSON missing required fields: {', '.join(sorted(missing))}."
            )

        label = str(payload["label"]).strip().lower()
        if label not in self.valid_labels:
            raise SentimentProviderError(f"Ollama sentiment label is invalid: {label}.")

        score = self._bounded_float(payload["score"], minimum=-1.0, maximum=1.0, field_name="score")
        confidence = self._bounded_float(
            payload["confidence"],
            minimum=0.0,
            maximum=1.0,
            field_name="confidence",
        )
        drivers = self._string_list(payload["drivers"], "drivers")
        evidence_snippets = self._string_list(payload["evidence_snippets"], "evidence_snippets")
        limitations = self._string_list(payload["limitations"], "limitations")

        return SentimentResult(
            label=label,
            score=round(score, 5),
            confidence=round(confidence, 5),
            drivers=drivers,
            evidence_snippets=evidence_snippets,
            limitations=limitations,
            provider=self.provider_name,
            model_name=self.model_name,
            model_version=f"{self.model_version}:{self.model}",
        )

    def _bounded_float(
        self,
        value: Any,
        *,
        minimum: float,
        maximum: float,
        field_name: str,
    ) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise SentimentProviderError(f"Ollama field {field_name} must be numeric.") from exc
        if parsed < minimum or parsed > maximum:
            raise SentimentProviderError(
                f"Ollama field {field_name} must be between {minimum} and {maximum}."
            )
        return parsed

    def _string_list(self, value: Any, field_name: str) -> list[str]:
        if isinstance(value, str):
            if field_name == "drivers":
                return [item.strip() for item in value.split(",") if item.strip()]
            stripped = value.strip()
            return [stripped] if stripped else []
        if not isinstance(value, list):
            raise SentimentProviderError(f"Ollama field {field_name} must be a list of strings.")
        items = [self._list_item_to_string(item, field_name) for item in value]
        return [item for item in items if item]

    def _list_item_to_string(self, item: Any, field_name: str) -> str:
        if isinstance(item, str):
            return item.strip()
        if field_name == "drivers" and isinstance(item, dict):
            for key in ("driver", "category", "name", "type"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        raise SentimentProviderError(f"Ollama field {field_name} must be a list of strings.")
