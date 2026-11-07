import logging
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import DATA_DIR, settings
from app.keys import KeyPool, is_retryable_provider_error
from app.rag.documents import knowledge_fingerprint, load_documents

logger = logging.getLogger(__name__)

HASH_FILE = DATA_DIR / "knowledge.sha256"
INDEX_VERSION = "gemini-embed-v1"


class GeminiEmbeddings(Embeddings):
    """Gemini embeddings. Documents and queries use different retrieval task types."""

    def __init__(self, pool: KeyPool, model: str) -> None:
        self._pool = pool
        self._model = model.strip().removeprefix("models/")

    def _client(self, api_key: str, task_type: str) -> GoogleGenerativeAIEmbeddings:
        return GoogleGenerativeAIEmbeddings(
            model=self._model,
            google_api_key=api_key,
            task_type=task_type,
        )

    def _embed(self, task_type: str, call):
        last_error: BaseException | None = None
        for api_key in self._pool.snapshot_order():
            try:
                result = call(self._client(api_key, task_type))
                self._pool.prefer(api_key)
                return result
            except Exception as exc:
                last_error = exc
                if not is_retryable_provider_error(exc):
                    raise
                logger.warning("Gemini embedding key failed; trying the next key. %s", exc)
                self._pool.rotate()
        raise RuntimeError("All Gemini API keys failed for embeddings.") from last_error

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed("RETRIEVAL_DOCUMENT", lambda client: client.embed_documents(texts))

    def embed_query(self, text: str) -> list[float]:
        return self._embed("RETRIEVAL_QUERY", lambda client: client.embed_query(text))


def build_embeddings() -> GeminiEmbeddings:
    keys = settings.gemini_keys
    if not keys:
        raise RuntimeError("Set at least one GEMINI_API_KEY. Chat and embeddings both use Gemini.")
    logger.info("Using Gemini embeddings %s with %s API key(s).", settings.gemini_embed_model, len(keys))
    return GeminiEmbeddings(KeyPool(keys, name="Gemini"), settings.gemini_embed_model)


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
    fingerprint = f"{INDEX_VERSION}:{settings.gemini_embed_model}:{knowledge_fingerprint()}"
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
