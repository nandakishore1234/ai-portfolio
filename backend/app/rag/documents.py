import hashlib
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import KNOWLEDGE_DIR

PINNED_TITLES = {"Who I Am", "Date of birth", "Current Role"}

_ORIGIN = re.compile(
    r"\b(?:from where|where are you from|where do you live|you are from|you're from|hometown|native place)\b",
    re.IGNORECASE,
)
_HOMETOWN_FACT = re.compile(
    r"\b(?:my hometown is|i am from|i live in|i was born in)\b",
    re.IGNORECASE,
)


def origin_reply(question: str) -> str | None:
    """A college or employer is not a hometown. Say so only when no note states one."""
    if not _ORIGIN.search(question):
        return None
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")) + sorted(KNOWLEDGE_DIR.glob("*.txt")):
        if _HOMETOWN_FACT.search(path.read_text(encoding="utf-8")):
            return None
    return "I don't have that detail here."


def pinned_documents() -> list[Document]:
    """Identity sections included with every answer so the model can use them."""
    return [doc for doc in load_documents() if doc.metadata.get("title") in PINNED_TITLES]


def knowledge_fingerprint() -> str:
    digest = hashlib.sha256()
    files = sorted(KNOWLEDGE_DIR.glob("*.md")) + sorted(KNOWLEDGE_DIR.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"Add .md or .txt files to {KNOWLEDGE_DIR}")
    for path in files:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_documents() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)
    documents: list[Document] = []
    files = sorted(KNOWLEDGE_DIR.glob("*.md")) + sorted(KNOWLEDGE_DIR.glob("*.txt"))
    for path in files:
        sections = _sections(path)
        for title, body in sections:
            for chunk in splitter.split_text(body):
                documents.append(
                    Document(page_content=f"{title}\n{chunk}", metadata={"title": title, "source": path.name})
                )
    if not documents:
        raise FileNotFoundError(f"No readable notes in {KNOWLEDGE_DIR}")
    return documents


def _sections(path: Path) -> list[tuple[str, str]]:
    title = path.stem
    sections: list[tuple[str, str]] = []
    body: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if body:
                sections.append((title, "\n".join(body).strip()))
            title = line[3:].strip()
            body = []
        else:
            body.append(line)
    if body and "\n".join(body).strip():
        sections.append((title, "\n".join(body).strip()))
    return [(name, text) for name, text in sections if text]
