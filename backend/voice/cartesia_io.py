from __future__ import annotations

import logging

from livekit.agents import APIConnectOptions, stt, tts, utils
from livekit.agents.types import NOT_GIVEN, NotGivenOr
from livekit.plugins import cartesia

from app.keys import KeyPool, is_retryable_provider_error

logger = logging.getLogger(__name__)


class FallbackCartesiaTTS(tts.TTS):
    def __init__(self, pool: KeyPool, voices: dict[str, str] | None = None, **opts) -> None:
        self._pool = pool
        self._voices = voices or {}
        self._opts = opts
        inner = cartesia.TTS(api_key=pool.current(), **self._tts_opts(pool.current()))
        super().__init__(
            capabilities=inner.capabilities,
            sample_rate=inner.sample_rate,
            num_channels=inner.num_channels,
        )
        self._inner = inner

    def _tts_opts(self, api_key: str) -> dict:
        opts = dict(self._opts)
        voice = (self._voices.get(api_key) or opts.get("voice") or "").strip()
        if voice:
            opts["voice"] = voice
        return opts

    def _client(self, api_key: str | None = None) -> cartesia.TTS:
        key = api_key or self._pool.current()
        self._inner = cartesia.TTS(api_key=key, **self._tts_opts(key))
        return self._inner

    def synthesize(self, text: str, *, conn_options: APIConnectOptions | None = None) -> tts.ChunkedStream:
        last_error: BaseException | None = None
        for api_key in self._pool.snapshot_order():
            try:
                stream = self._client(api_key).synthesize(text, conn_options=conn_options or APIConnectOptions())
                self._pool.prefer(api_key)
                return stream
            except Exception as exc:
                last_error = exc
                if not is_retryable_provider_error(exc):
                    raise
                logger.warning("Cartesia TTS key failed; trying the next key. %s", exc)
                self._pool.rotate()
        raise RuntimeError("All Cartesia TTS API keys failed.") from last_error

    def stream(self, *, conn_options: APIConnectOptions | None = None):
        # AgentSession uses streaming TTS. The wrapper must forward stream(), not only synthesize().
        last_error: BaseException | None = None
        for api_key in self._pool.snapshot_order():
            try:
                stream = self._client(api_key).stream(conn_options=conn_options or APIConnectOptions())
                self._pool.prefer(api_key)
                return stream
            except Exception as exc:
                last_error = exc
                if not is_retryable_provider_error(exc):
                    raise
                logger.warning("Cartesia TTS stream key failed; trying the next key. %s", exc)
                self._pool.rotate()
        raise RuntimeError("All Cartesia TTS API keys failed.") from last_error


class FallbackCartesiaSTT(stt.STT):
    def __init__(self, pool: KeyPool, **opts) -> None:
        inner = cartesia.STT(api_key=pool.current(), **opts)
        super().__init__(capabilities=inner.capabilities)
        self._pool = pool
        self._opts = opts
        self._inner = inner

    def _rebuild(self, api_key: str) -> None:
        self._inner = cartesia.STT(api_key=api_key, **self._opts)

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        last_error: BaseException | None = None
        for api_key in self._pool.snapshot_order():
            try:
                self._rebuild(api_key)
                event = await self._inner._recognize_impl(buffer, language=language, conn_options=conn_options)
                self._pool.prefer(api_key)
                return event
            except Exception as exc:
                last_error = exc
                if not is_retryable_provider_error(exc):
                    raise
                logger.warning("Cartesia STT key failed; trying the next key. %s", exc)
                self._pool.rotate()
        raise RuntimeError("All Cartesia STT API keys failed.") from last_error

    def stream(self, **kwargs):
        last_error: BaseException | None = None
        for api_key in self._pool.snapshot_order():
            try:
                self._rebuild(api_key)
                stream = self._inner.stream(**kwargs)
                self._pool.prefer(api_key)
                return stream
            except Exception as exc:
                last_error = exc
                if not is_retryable_provider_error(exc):
                    raise
                logger.warning("Cartesia STT stream key failed; trying the next key. %s", exc)
                self._pool.rotate()
        raise RuntimeError("All Cartesia STT API keys failed.") from last_error
