from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ...config import settings


class AssistantProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingBatch:
    embeddings: list[list[float]]
    provider: str
    model: str


def normalize_provider(value: str | None) -> str:
    return (value or "ollama").strip().lower()


def get_chat_provider() -> str:
    return normalize_provider(settings.assistant_provider)


def get_embedding_provider() -> str:
    return normalize_provider(settings.assistant_embedding_provider)


def get_embedding_config() -> tuple[str, str]:
    return get_embedding_provider(), settings.assistant_embedding_model


def embed_texts(texts: list[str]) -> EmbeddingBatch:
    provider = get_embedding_provider()
    normalized_texts = [text.strip() for text in texts]
    if not normalized_texts:
        return EmbeddingBatch(embeddings=[], provider=provider, model=settings.assistant_embedding_model)

    if provider == "openai":
        return _embed_with_openai(normalized_texts)
    if provider == "ollama":
        return _embed_with_ollama(normalized_texts)

    raise AssistantProviderError(f"Unsupported embedding provider: {provider}")


def chat_complete(messages: list[dict[str, str]], *, temperature: float = 0.1) -> str:
    provider = get_chat_provider()
    if provider == "openai":
        return _chat_with_openai(messages, temperature=temperature)
    if provider == "ollama":
        return _chat_with_ollama(messages, temperature=temperature)
    raise AssistantProviderError(f"Unsupported assistant provider: {provider}")


def _embed_with_openai(texts: list[str]) -> EmbeddingBatch:
    if not settings.openai_api_key:
        raise AssistantProviderError("OPENAI_API_KEY is required when ASSISTANT_EMBEDDING_PROVIDER=openai.")

    payload = {
        "model": settings.assistant_embedding_model,
        "input": texts,
    }
    parsed = _json_request(
        f"{settings.openai_base_url.rstrip('/')}/embeddings",
        payload=payload,
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
    )
    data = parsed.get("data")
    if not isinstance(data, list):
        raise AssistantProviderError("OpenAI embeddings response did not contain a data array.")

    ordered = sorted(data, key=lambda item: int(item.get("index", 0)) if isinstance(item, dict) else 0)
    embeddings: list[list[float]] = []
    for item in ordered:
        embedding = item.get("embedding") if isinstance(item, dict) else None
        if not isinstance(embedding, list):
            raise AssistantProviderError("OpenAI embeddings response contained an invalid embedding.")
        embeddings.append([float(value) for value in embedding])

    return EmbeddingBatch(embeddings=embeddings, provider="openai", model=settings.assistant_embedding_model)


def _embed_with_ollama(texts: list[str]) -> EmbeddingBatch:
    payload = {
        "model": settings.assistant_embedding_model,
        "input": texts,
    }
    try:
        parsed = _json_request(f"{settings.assistant_embedding_base_url.rstrip('/')}/api/embed", payload=payload)
        embeddings = parsed.get("embeddings")
        if isinstance(embeddings, list):
            return EmbeddingBatch(
                embeddings=[[float(value) for value in embedding] for embedding in embeddings],
                provider="ollama",
                model=settings.assistant_embedding_model,
            )
    except AssistantProviderError:
        pass

    # Older Ollama versions expose only /api/embeddings and accept one prompt at a time.
    embeddings = []
    for text in texts:
        parsed = _json_request(
            f"{settings.assistant_embedding_base_url.rstrip('/')}/api/embeddings",
            payload={"model": settings.assistant_embedding_model, "prompt": text},
        )
        embedding = parsed.get("embedding")
        if not isinstance(embedding, list):
            raise AssistantProviderError("Ollama embeddings response did not contain an embedding array.")
        embeddings.append([float(value) for value in embedding])

    return EmbeddingBatch(embeddings=embeddings, provider="ollama", model=settings.assistant_embedding_model)


def _chat_with_openai(messages: list[dict[str, str]], *, temperature: float) -> str:
    if not settings.openai_api_key:
        raise AssistantProviderError("OPENAI_API_KEY is required when ASSISTANT_PROVIDER=openai.")

    payload = {
        "model": settings.assistant_model,
        "messages": messages,
        "temperature": temperature,
    }
    parsed = _json_request(
        f"{settings.openai_base_url.rstrip('/')}/chat/completions",
        payload=payload,
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
    )
    choices = parsed.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AssistantProviderError("OpenAI chat response did not contain choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise AssistantProviderError("OpenAI chat response was empty.")
    return content.strip()


def _chat_with_ollama(messages: list[dict[str, str]], *, temperature: float) -> str:
    payload = {
        "model": settings.assistant_model,
        "stream": False,
        "keep_alive": "15m",
        "options": {"temperature": temperature},
        "messages": messages,
    }
    parsed = _json_request(f"{settings.assistant_base_url.rstrip('/')}/api/chat", payload=payload)
    message = parsed.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise AssistantProviderError("Ollama chat response was empty.")
    return content.strip()


def _json_request(url: str, *, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        **(headers or {}),
    }
    request = Request(url=url, data=body, headers=request_headers, method="POST")

    try:
        with urlopen(request, timeout=settings.assistant_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise AssistantProviderError(_extract_provider_error(raw) or f"Provider request failed with status {exc.code}.") from exc
    except URLError as exc:
        raise AssistantProviderError(f"Provider is not reachable at {url}.") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssistantProviderError("Provider returned a non-JSON response.") from exc

    if not isinstance(parsed, dict):
        raise AssistantProviderError("Provider returned an unexpected response shape.")
    if parsed.get("error"):
        raise AssistantProviderError(str(parsed["error"]))
    return parsed


def _extract_provider_error(raw: str) -> str | None:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip() or None
    if isinstance(parsed, dict) and parsed.get("error"):
        return str(parsed["error"]).strip()
    return raw.strip() or None


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
