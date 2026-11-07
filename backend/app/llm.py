from __future__ import annotations

import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from app.config import settings
from app.keys import KeyPool, is_retryable_provider_error

logger = logging.getLogger(__name__)


class FallbackChat:
    """Tries Gemini keys in order; rotates after quota/auth failures."""

    def __init__(self, pool: KeyPool, model: str) -> None:
        self._pool = pool
        self._model = model

    def _client(self, api_key: str):
        # gemini-*-flash-lite ignores sampling params; do not pass temperature.
        return ChatGoogleGenerativeAI(model=self._model, api_key=api_key)

    def invoke(self, messages, **kwargs):
        last_error: BaseException | None = None
        for api_key in self._pool.snapshot_order():
            try:
                result = self._client(api_key).invoke(messages, **kwargs)
                self._pool.prefer(api_key)
                return result
            except Exception as exc:
                last_error = exc
                if not is_retryable_provider_error(exc):
                    raise
                logger.warning("Gemini key failed; trying the next key. %s", exc)
                self._pool.rotate()
        raise RuntimeError("All Gemini API keys failed.") from last_error


def build_chat_llm():
    keys = settings.gemini_keys
    if keys:
        logger.info("Using Gemini model %s with %s API key(s).", settings.gemini_model, len(keys))
        return FallbackChat(KeyPool(keys, name="Gemini"), settings.gemini_model)
    logger.info("No Gemini keys set; using Ollama %s.", settings.ollama_chat_model)
    return ChatOllama(
        model=settings.ollama_chat_model,
        base_url=settings.ollama_base_url,
        temperature=0.2,
    )
