from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama

from agent.graph import build_rag_graph
from app.api.chat import router as chat_router
from app.api.contact import router as contact_router
from app.config import settings
from app.rag.store import build_client, build_embeddings, build_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    app.state.error = None
    try:
        embeddings = build_embeddings()
        client = build_client()
        store = build_store(client, embeddings)
        llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
        )
        app.state.graph = build_rag_graph(llm, store, settings.rag_top_k)
        app.state.ready = True
    except Exception as exc:
        app.state.error = (
            "The assistant could not start. Check that Ollama is running with "
            f"{settings.ollama_chat_model} and {settings.ollama_embed_model}, and that Qdrant is reachable. {exc}"
        )
    yield


app = FastAPI(title="Nanda Portfolio Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router, prefix="/api")
app.include_router(contact_router, prefix="/api")
