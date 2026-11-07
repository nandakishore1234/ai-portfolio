from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.runtime import build_rag_stack
from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.contact import router as contact_router
from app.api.livekit import router as livekit_router
from app.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    app.state.error = None
    try:
        init_db()
        app.state.graph = build_rag_stack(for_voice=False)
        app.state.ready = True
    except Exception as exc:
        app.state.error = (
            "The assistant could not start. Check Gemini keys (or Ollama), "
            f"{settings.ollama_embed_model} embeddings, and Qdrant. {exc}"
        )
    yield


app = FastAPI(title="Nanda Portfolio Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router, prefix="/api")
app.include_router(contact_router, prefix="/api")
app.include_router(livekit_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
