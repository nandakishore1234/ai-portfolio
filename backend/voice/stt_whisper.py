from __future__ import annotations

import logging
import time
from typing import Literal

import numpy as np
from faster_whisper import WhisperModel
from livekit.agents import APIConnectOptions, stt, utils
from livekit.agents.types import NOT_GIVEN, NotGivenOr

logger = logging.getLogger(__name__)

ModelSize = Literal[
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v2",
    "large-v3",
]


class FasterWhisperSTT(stt.STT):
    def __init__(
        self,
        *,
        model_size: ModelSize | str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "en",
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> None:
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        self._language = language
        self._beam_size = beam_size
        self._vad_filter = vad_filter
        logger.info("Loading FasterWhisper model=%s device=%s compute=%s", model_size, device, compute_type)
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("FasterWhisper ready")

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        if isinstance(buffer, list):
            chunks = [np.frombuffer(frame.data, dtype=np.int16) for frame in buffer]
            audio_data = np.concatenate(chunks).astype(np.float32) / 32768.0
        else:
            audio_data = np.frombuffer(buffer.data, dtype=np.int16).astype(np.float32) / 32768.0

        lang = language if language is not NOT_GIVEN else self._language
        started = time.perf_counter()
        segments, info = self._model.transcribe(
            audio_data,
            beam_size=self._beam_size,
            best_of=self._beam_size,
            temperature=0.0,
            vad_filter=self._vad_filter,
            language=lang,
        )
        text = "".join(segment.text for segment in segments).strip()
        # Drop empty / tiny noise so the agent does not reply "I didn't catch that".
        if len(text) < 2:
            text = ""
        logger.debug("STT %.0fms duration=%.1fs text=%r", (time.perf_counter() - started) * 1000, info.duration, text)
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(text=text, language=lang or "")],
        )
