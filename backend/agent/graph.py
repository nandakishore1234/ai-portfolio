import re
from datetime import date

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from agent.prompts import ANSWER_PROMPT, REWRITE_PROMPT, VOICE_ANSWER_PROMPT
from agent.state import GraphState
from app.rag.documents import origin_reply, pinned_documents


def _fill(template: str, **values: str) -> str:
    text = template
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text


def _text(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or ""))
        return "".join(parts).strip()
    return str(content or "").strip()


_FOLLOW_UP = re.compile(
    r"\b(it|that|this|those|these|there|they|them|he|she|his|her|their|one|same)\b",
    re.IGNORECASE,
)


def build_rag_graph(llm, vector_store, top_k: int):
    def rewrite(state: GraphState):
        # Voice skips the extra rewrite LLM call to cut turn latency.
        if state.get("mode") == "voice":
            return {"standalone_question": state["question"]}
        if not state["history"].strip() or not _FOLLOW_UP.search(state["question"]):
            return {"standalone_question": state["question"]}
        message = llm.invoke(
            [HumanMessage(content=_fill(REWRITE_PROMPT, history=state["history"], question=state["question"]))]
        )
        text = _text(message) or state["question"]
        return {"standalone_question": text}

    def retrieve(state: GraphState):
        docs = list(vector_store.similarity_search(state["standalone_question"], k=top_k))
        seen = {doc.page_content for doc in docs}
        for doc in pinned_documents():
            if doc.page_content not in seen:
                docs.append(doc)
                seen.add(doc.page_content)
        return {"context": docs}

    def generate(state: GraphState):
        missing_place = origin_reply(state["question"])
        if missing_place:
            return {"context": [], "answer": missing_place}
        if state["context"]:
            context = "\n\n".join(
                f"[{doc.metadata.get('title', 'Notes')}]\n{doc.page_content}" for doc in state["context"]
            )
        else:
            context = "No matching notes."
        prompt = VOICE_ANSWER_PROMPT if state.get("mode") == "voice" else ANSWER_PROMPT
        fill_kwargs = {
            "today": date.today().strftime("%d %B %Y"),
            "context": context,
            "question": state["question"],
        }
        if prompt is ANSWER_PROMPT:
            fill_kwargs["history"] = state["history"] or "None"
        message = llm.invoke([HumanMessage(content=_fill(prompt, **fill_kwargs))])
        return {"answer": _text(message)}

    graph = StateGraph(GraphState)
    graph.add_node("rewrite", rewrite)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "rewrite")
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
