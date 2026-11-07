from __future__ import annotations

import asyncio
import io
import logging
import time
import uuid
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from livekit.agents import APIConnectOptions, tts

if TYPE_CHECKING:
    from livekit.agents.tts.tts import AudioEmitter

logger = logging.getLogger(__name__)


class _PiperChunkedStream(tts.ChunkedStream):
    def __init__(self, *, tts_plugin: "PiperTTS", input_text: str, conn_options: APIConnectOptions) -> None:
        super().__init__(tts=tts_plugin, input_text=input_text, conn_options=conn_options)
        self._piper_tts = tts_plugin

    async def _run(self, output_emitter: "AudioEmitter") -> None:
        output_emitter.initialize(
            request_id=str(uuid.uuid4()),
            sample_rate=self._piper_tts.sample_rate,
            num_channels=self._piper_tts.num_channels,
            mime_type="audio/pcm",
        )
        loop = asyncio.get_running_loop()
        started = time.perf_counter()
        audio_bytes = await loop.run_in_executor(None, self._synthesize_blocking, self._input_text)
        logger.debug("TTS %.0fms chars=%s", (time.perf_counter() - started) * 1000, len(self._input_text))
        output_emitter.push(audio_bytes)

    def _synthesize_blocking(self, text: str) -> bytes:
        from piper.config import SynthesisConfig

        syn_config = SynthesisConfig(
            length_scale=1.0 / max(self._piper_tts.speed, 0.1),
            noise_scale=self._piper_tts.noise_scale,
            noise_w_scale=self._piper_tts.noise_w,
            volume=self._piper_tts.volume,
        )
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
            self._piper_tts.voice.synthesize_wav(text, wav_file, syn_config=syn_config, set_wav_format=True)
        wav_io.seek(0)
        with wave.open(wav_io, "rb") as wav_file:
            return wav_file.readframes(wav_file.getnframes())


class PiperTTS(tts.TTS):
    def __init__(
        self,
        model_path: str | Path,
        *,
        use_cuda: bool = False,
        speed: float = 1.0,
        volume: float = 1.0,
        noise_scale: float = 0.667,
        noise_w: float = 0.8,
    ) -> None:
        from piper.voice import PiperVoice

        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Piper model not found at {path}. Download en_US-ryan-high.onnx and .onnx.json "
                "into backend/data/piper/ (see README)."
            )

        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=22050,
            num_channels=1,
        )
        self.speed = speed
        self.volume = volume
        self.noise_scale = noise_scale
        self.noise_w = noise_w
        logger.info("Loading Piper voice from %s", path)
        self.voice = PiperVoice.load(str(path), use_cuda=use_cuda)
        logger.info("Piper ready")

    def synthesize(self, text: str, *, conn_options: APIConnectOptions | None = None) -> tts.ChunkedStream:
        return _PiperChunkedStream(
            tts_plugin=self,
            input_text=text,
            conn_options=conn_options or APIConnectOptions(),
        )
