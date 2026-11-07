"""LiveKit voice worker: Cartesia STT → shared RAG LLM → Cartesia TTS.

Chat stays on FastAPI. Voice does not call /api/chat.
Run from backend/:
  .\\.venv\\Scripts\\python -m voice.agent start
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from livekit.agents import Agent, AgentSession, JobContext, JobProcess, RunContext, WorkerOptions, cli, function_tool
from livekit.plugins import langchain, silero

from agent.runtime import get_voice_rag_stack
from agent.voice_graph import build_voice_rag_graph
from app.config import settings
from app.db import init_db
from app.keys import KeyPool
from voice.cartesia_io import FallbackCartesiaSTT, FallbackCartesiaTTS
from voice.recorder import CallRecorder
from voice.stt_whisper import FasterWhisperSTT
from voice.tts_piper import PiperTTS

logger = logging.getLogger("voice.agent")


def _export_livekit_env() -> None:
    """LiveKit CLI reads os.environ; pydantic Settings alone is not enough."""
    os.environ.setdefault("LIVEKIT_URL", settings.livekit_url)
    os.environ.setdefault("LIVEKIT_API_KEY", settings.livekit_api_key)
    os.environ.setdefault("LIVEKIT_API_SECRET", settings.livekit_api_secret)
    if settings.cartesia_keys:
        os.environ.setdefault("CARTESIA_API_KEY", settings.cartesia_keys[0])
    if settings.gemini_keys:
        os.environ.setdefault("GOOGLE_API_KEY", settings.gemini_keys[0])


VOICE_INSTRUCTIONS = (
    "You are Nanda Kishore speaking on a voice call as yourself, the person. "
    "Keep answers short, spoken, and first person. No markdown or emojis. "
    "If asked to explain yourself, introduce your work as a person. "
    "Do not describe STT, TTS, LLMs, or how this call agent is built. "
    "When the visitor says bye, goodbye, that's all, talk later, or wants to end the call, "
    "say one short goodbye and call hang_up_call after that goodbye."
)

WELCOME_MESSAGE = "Hey! I'm Nandakishore. Feel free to explore my work, projects, and experience. What would you like to know?"


class NandaVoiceAgent(Agent):
    def __init__(self, hangup_state: dict) -> None:
        super().__init__(instructions=VOICE_INSTRUCTIONS)
        self._hangup_state = hangup_state

    @function_tool()
    async def hang_up_call(self, context: RunContext) -> str:
        """End the call after you have said goodbye. Use when the visitor is leaving."""
        self._hangup_state["pending"] = True
        return "Say a short goodbye, then the call will hang up."


def _build_stt():
    keys = settings.cartesia_keys
    if keys:
        logger.info("Using Cartesia STT (%s) with %s key(s).", settings.cartesia_stt_model, len(keys))
        return FallbackCartesiaSTT(
            KeyPool(keys, name="Cartesia"),
            model=settings.cartesia_stt_model,
            language=settings.cartesia_stt_language,
        )
    logger.info("No Cartesia keys set; using local Faster-Whisper.")
    return FasterWhisperSTT(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        language="en",
    )


def _build_tts():
    keys = settings.cartesia_keys
    if keys:
        voices = settings.cartesia_key_voices
        logger.info(
            "Using Cartesia TTS (%s) with %s key/voice pair(s).",
            settings.cartesia_tts_model,
            len(keys),
        )
        return FallbackCartesiaTTS(
            KeyPool(keys, name="Cartesia"),
            voices=voices,
            model=settings.cartesia_tts_model,
            language=settings.cartesia_tts_language,
            voice=settings.cartesia_tts_voice_id,
            speed=settings.cartesia_tts_speed,
        )
    logger.info("No Cartesia keys set; using local Piper.")
    return PiperTTS(settings.piper_model_file, speed=settings.piper_speed, use_cuda=False)


def prewarm(proc: JobProcess) -> None:
    logger.info("Prewarming voice session…")
    proc.userdata["vad"] = silero.VAD.load()
    proc.userdata["stt"] = _build_stt()
    proc.userdata["tts"] = _build_tts()
    proc.userdata["rag"] = get_voice_rag_stack()
    logger.info("Voice session ready")


def _build_session(ctx: JobContext, hangup_state: dict) -> AgentSession:
    userdata = ctx.proc.userdata
    rag = userdata.get("rag") or get_voice_rag_stack()
    return AgentSession(
        vad=userdata.get("vad") or silero.VAD.load(),
        stt=userdata.get("stt") or _build_stt(),
        llm=langchain.LLMAdapter(graph=build_voice_rag_graph(rag, hangup_state)),
        tts=userdata.get("tts") or _build_tts(),
        min_endpointing_delay=0.6,
        max_endpointing_delay=3.0,
        min_interruption_words=1,
    )


def _agent_is_speaking(session: AgentSession) -> bool:
    state = str(getattr(session, "agent_state", "")).lower()
    return "speak" in state or "think" in state


async def _hang_up(ctx: JobContext, session: AgentSession, recorder: CallRecorder | None = None) -> None:
    logger.info("Hanging up room %s after goodbye", ctx.room.name)
    if recorder:
        try:
            await recorder.finalize()
        except Exception as exc:
            logger.warning("Recording finalize failed: %s", exc)
    try:
        await session.aclose()
    except Exception:
        pass
    try:
        from livekit.api import DeleteRoomRequest

        await ctx.api.room.delete_room(DeleteRoomRequest(room=ctx.room.name))
    except Exception as exc:
        logger.warning("Room delete failed (%s); disconnecting instead.", exc)
        try:
            await ctx.room.disconnect()
        except Exception:
            pass


async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info("Voice agent joining room %s", ctx.room.name)
    init_db()
    hangup_state = {"pending": False, "closing": False}
    recorder = CallRecorder(ctx.room.name)
    recorder.attach(ctx.room)
    session = _build_session(ctx, hangup_state)
    await ctx.connect()
    await session.start(
        agent=NandaVoiceAgent(hangup_state),
        room=ctx.room,
    )
    await session.say(WELCOME_MESSAGE, allow_interruptions=True)

    async def on_shutdown() -> None:
        try:
            await recorder.finalize()
        except Exception as exc:
            logger.warning("Shutdown recording finalize failed: %s", exc)

    if hasattr(ctx, "add_shutdown_callback"):
        ctx.add_shutdown_callback(on_shutdown)

    async def watch_hangup() -> None:
        while True:
            await asyncio.sleep(0.2)
            if hangup_state["pending"] and not hangup_state["closing"]:
                hangup_state["closing"] = True
                for _ in range(40):
                    if not _agent_is_speaking(session):
                        break
                    await asyncio.sleep(0.15)
                await asyncio.sleep(0.6)
                await _hang_up(ctx, session, recorder)
                return

    asyncio.create_task(watch_hangup())


if __name__ == "__main__":
    _export_livekit_env()
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            initialize_process_timeout=120.0,
            num_idle_processes=max(1, settings.voice_idle_processes),
        )
    )
