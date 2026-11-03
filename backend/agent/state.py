from typing import TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict):
    question: str
    history: str
    standalone_question: str
    context: list[Document]
    answer: str
