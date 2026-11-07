"""Record LiveKit audio into one mixed call WAV, then store it."""

from __future__ import annotations

import asyncio
import io
import logging
import wave

import numpy as np
from livekit import rtc

from app.db import insert_asset
from app.seaweed import call_object_path, public_url, upload_bytes

logger = logging.getLogger(__name__)


class CallRecorder:
    def __init__(self, room_name: str) -> None:
        self.room_name = room_name
        self._chunks: dict[str, list[bytes]] = {}
        self._format: dict[str, tuple[int, int]] = {}
        self._tasks: list[asyncio.Task] = []
        self._streams: list = []
        self._stop = asyncio.Event()
        self._done = False
        self._started: set[str] = set()

    def _role(self, identity: str) -> str:
        name = (identity or "").lower()
        if name.startswith("agent") or name in {"agent", "nanda"}:
            return "agent"
        return "visitor"

    def _start_track(self, identity: str, track) -> None:
        if getattr(track, "kind", None) != rtc.TrackKind.KIND_AUDIO:
            return
        sid = str(getattr(track, "sid", "") or identity)
        if sid in self._started or self._done:
            return
        self._started.add(sid)
        logger.info("Recording audio from %s", identity)
        self._tasks.append(asyncio.create_task(self._capture(identity, track), name=f"rec-{identity}"))

    def attach(self, room: rtc.Room) -> None:
        @room.on("track_subscribed")
        def _on_subscribed(track, publication, participant) -> None:
            identity = getattr(participant, "identity", "") or "visitor"
            self._start_track(identity, track)

        @room.on("local_track_published")
        def _on_local(publication, track=None) -> None:
            audio = track or getattr(publication, "track", None)
            if audio is not None:
                self._start_track("agent", audio)

        @room.on("track_published")
        def _on_published(publication, participant) -> None:
            if getattr(participant, "identity", "") in {"agent", "nanda"}:
                return
            audio = getattr(publication, "track", None)
            identity = getattr(participant, "identity", "") or "publisher"
            if audio is not None:
                self._start_track(identity, audio)

    async def _capture(self, identity: str, track) -> None:
        self._chunks.setdefault(identity, [])
        stream = None
        try:
            stream = rtc.AudioStream(track)
            self._streams.append(stream)
            async for event in stream:
                if self._stop.is_set() or self._done:
                    break
                frame = getattr(event, "frame", event)
                self._chunks[identity].append(bytes(frame.data))
                self._format[identity] = (int(frame.sample_rate), int(frame.num_channels))
        except asyncio.CancelledError:
            return
        except RuntimeError as exc:
            if "loop" not in str(exc).lower():
                logger.warning("Audio capture stopped for %s: %s", identity, exc)
        except Exception as exc:
            logger.warning("Audio capture stopped for %s: %s", identity, exc)
        finally:
            if stream is not None:
                closer = getattr(stream, "aclose", None) or getattr(stream, "close", None)
                if closer:
                    try:
                        result = closer()
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception:
                        pass

    def _pcm(self, identity: str) -> tuple[np.ndarray, int]:
        pieces = self._chunks.get(identity) or []
        sample_rate, channels = self._format.get(identity, (48000, 1))
        if not pieces:
            return np.zeros(0, dtype=np.int16), sample_rate or 48000
        samples = np.frombuffer(b"".join(pieces), dtype=np.int16)
        channels = max(int(channels or 1), 1)
        if channels > 1:
            usable = (len(samples) // channels) * channels
            samples = samples[:usable].reshape(-1, channels).mean(axis=1).astype(np.int16)
        return samples, sample_rate or 48000

    def _overlay(self, first: np.ndarray, second: np.ndarray) -> np.ndarray:
        if first.size == 0:
            return second
        if second.size == 0:
            return first
        length = max(int(first.size), int(second.size))
        mixed = np.zeros(length, dtype=np.int32)
        mixed[: first.size] += first.astype(np.int32)
        mixed[: second.size] += second.astype(np.int32)
        return np.clip(mixed, -32768, 32767).astype(np.int16)

    def _mixed_wav(self) -> bytes | None:
        visitor = np.zeros(0, dtype=np.int16)
        agent = np.zeros(0, dtype=np.int16)
        sample_rate = 48000
        for identity in self._chunks:
            pcm, rate = self._pcm(identity)
            if pcm.size == 0:
                continue
            sample_rate = rate
            if self._role(identity) == "agent":
                agent = self._overlay(agent, pcm)
            else:
                visitor = self._overlay(visitor, pcm)
        if visitor.size == 0 and agent.size == 0:
            return None
        length = max(int(visitor.size), int(agent.size), 1)
        left = np.zeros(length, dtype=np.int16)
        right = np.zeros(length, dtype=np.int16)
        if visitor.size:
            left[: visitor.size] = visitor
        if agent.size:
            right[: agent.size] = agent
        if visitor.size and not agent.size:
            right = left.copy()
        if agent.size and not visitor.size:
            left = right.copy()
        stereo = np.column_stack((left, right)).reshape(-1)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(stereo.tobytes())
        return buffer.getvalue()

    async def finalize(self) -> list[int]:
        if self._done:
            return []
        self._done = True
        self._stop.set()
        for stream in list(self._streams):
            closer = getattr(stream, "aclose", None) or getattr(stream, "close", None)
            if not closer:
                continue
            try:
                result = closer()
                if asyncio.iscoroutine(result):
                    await asyncio.wait_for(result, timeout=1)
            except Exception:
                pass
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        wav = await asyncio.to_thread(self._mixed_wav)
        if not wav:
            logger.info("No audio frames captured for room %s", self.room_name)
            return []
        storage_path = call_object_path(self.room_name, "call")
        stored = await asyncio.to_thread(upload_bytes, storage_path, wav, "audio/wav")
        asset_id = insert_asset(
            room=self.room_name,
            kind="call-recording",
            identity="call",
            storage_path=stored,
            public_url=public_url(stored) if stored.startswith("/") else stored,
            mime_type="audio/wav",
            size_bytes=len(wav),
        )
        logger.info("Stored mixed call recording asset id=%s path=%s", asset_id, stored)
        return [asset_id]
