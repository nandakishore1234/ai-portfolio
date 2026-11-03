from fastapi import APIRouter, HTTPException, Request

from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.get("/health")
def health(request: Request):
    ready = bool(getattr(request.app.state, "ready", False))
    return {"ok": ready, "detail": getattr(request.app.state, "error", None)}


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, request: Request):
    if not getattr(request.app.state, "ready", False):
        detail = getattr(request.app.state, "error", None) or "The assistant is still starting."
        raise HTTPException(status_code=503, detail=detail)

    latest = body.messages[-1]
    if latest.role != "user":
        raise HTTPException(status_code=422, detail="The latest message must be from the visitor.")

    history = "\n".join(
        f"{'Visitor' if message.role == 'user' else 'Nanda'}: {message.content}"
        for message in body.messages[:-1]
    )
    try:
        result = request.app.state.graph.invoke(
            {
                "question": latest.content.strip(),
                "history": history,
                "standalone_question": "",
                "context": [],
                "answer": "",
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"The model could not answer: {exc}") from exc

    sources: list[str] = []
    for doc in result.get("context") or []:
        title = str(doc.metadata.get("title") or "").strip()
        if title and title not in sources:
            sources.append(title)
    return ChatResponse(reply=result.get("answer") or "I don't have that detail here.", sources=sources[:4])
