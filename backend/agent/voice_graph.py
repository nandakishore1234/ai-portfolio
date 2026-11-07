from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from agent.closing import GOODBYE_LINE, is_closing_utterance


def _message_text(message: BaseMessage) -> str:
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


class VoiceState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_voice_rag_graph(rag_graph, hangup_state: dict | None = None):
    """LiveKit LLMAdapter graph: STT text → shared RAG → spoken reply.

    Per-call hangup_state is set when the visitor uses a closing phrase.
    """

    def answer(state: VoiceState):
        payload_messages = []
        for message in state["messages"]:
            text = _message_text(message)
            if not text:
                continue
            if isinstance(message, HumanMessage) or getattr(message, "type", "") == "human":
                payload_messages.append({"role": "user", "content": text})
            elif isinstance(message, AIMessage) or getattr(message, "type", "") == "ai":
                payload_messages.append({"role": "assistant", "content": text})

        if not payload_messages or payload_messages[-1]["role"] != "user":
            return {"messages": [AIMessage(content="")]}

        latest = payload_messages[-1]["content"].strip()
        if len(latest) < 2 or latest.lower() in {".", "?", "...", "hmm", "uh", "um", "ah"}:
            return {"messages": [AIMessage(content="")]}

        if is_closing_utterance(latest):
            if hangup_state is not None:
                hangup_state["pending"] = True
            return {"messages": [AIMessage(content=GOODBYE_LINE)]}

        payload_messages = payload_messages[-20:]
        history = "\n".join(
            f"{'Visitor' if item['role'] == 'user' else 'Nanda'}: {item['content']}"
            for item in payload_messages[:-1]
        )
        try:
            result = rag_graph.invoke(
                {
                    "question": latest,
                    "history": history,
                    "standalone_question": "",
                    "context": [],
                    "answer": "",
                    "mode": "voice",
                }
            )
            reply = str(result.get("answer") or "").strip() or "I don't have that detail here."
        except Exception:
            reply = "I am having trouble reaching my notes right now. Please try again in a moment."
        if hangup_state is not None and is_closing_utterance(reply):
            hangup_state["pending"] = True
        return {"messages": [AIMessage(content=reply)]}

    graph = StateGraph(VoiceState)
    graph.add_node("answer", answer)
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)
    return graph.compile()
