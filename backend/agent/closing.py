import re

_CLOSING = re.compile(
    r"\b("
    r"bye|goodbye|good bye|see you|see ya|catch you later|"
    r"that'?s all|that is all|i'?m done|i am done|"
    r"talk later|take care|gotta go|got to go|have to go|"
    r"hang up|end (the )?call|disconnect|"
    r"have a good (one|day|night|evening)"
    r")\b",
    re.IGNORECASE,
)

GOODBYE_LINE = "Alright, take care. Bye."


def is_closing_utterance(text: str) -> bool:
    return bool(text and _CLOSING.search(text.strip()))
