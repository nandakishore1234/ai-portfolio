from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import DATA_DIR, settings
from app.rag.documents import knowledge_fingerprint, load_documents

HASH_FILE = DATA_DIR / "knowledge.sha256"
INDEX_VERSION = "nomic-prefix-v1"


class NomicEmbeddings(Embeddings):
    """nomic-embed-text expects search_query and search_document prefixes."""

    def __init__(self, inner: OllamaEmbeddings):
        self.inner = inner

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.inner.embed_documents([f"search_document: {text}" for text in texts])

    def embed_query(self, text: str) -> list[float]:
        return self.inner.embed_query(f"search_query: {text}")


def build_embeddings() -> NomicEmbeddings:
    return NomicEmbeddings(
        OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
    )


def build_client(*, local_name: str | None = None, in_memory: bool = False) -> QdrantClient:
    if in_memory:
        return QdrantClient(":memory:")
    raw = settings.qdrant_path.strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = DATA_DIR / path
        if local_name:
            path = path.parent / local_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(path))
    api_key = settings.qdrant_api_key.strip() or None
    return QdrantClient(url=settings.qdrant_url, api_key=api_key)


def build_store(
    client: QdrantClient,
    embeddings: Embeddings,
    *,
    hash_file: Path | None = None,
) -> QdrantVectorStore:
    _ensure_index(client, embeddings, hash_file=hash_file or HASH_FILE)
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )


def _ensure_index(client: QdrantClient, embeddings: Embeddings, *, hash_file: Path) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fingerprint = f"{INDEX_VERSION}:{settings.ollama_embed_model}:{knowledge_fingerprint()}"
    names = {item.name for item in client.get_collections().collections}
    stored = hash_file.read_text(encoding="utf-8").strip() if hash_file.exists() else ""
    if settings.qdrant_collection in names and stored == fingerprint:
        return

    probe = embeddings.embed_query("portfolio")
    if settings.qdrant_collection in names:
        client.delete_collection(settings.qdrant_collection)
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(size=len(probe), distance=Distance.COSINE),
    )
    documents = load_documents()
    store = QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )
    store.add_documents(documents, ids=[str(uuid5(NAMESPACE_URL, doc.page_content)) for doc in documents])
    hash_file.write_text(fingerprint, encoding="utf-8")
