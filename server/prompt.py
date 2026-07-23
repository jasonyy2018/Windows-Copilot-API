"""Flatten an OpenAI ``messages`` array into a single Copilot prompt.

Copilot's protocol has no role/system channel — it takes one prompt string per
turn — so we collapse the whole conversation into one piece of text.
"""

from typing import Any, List, Optional, Union

from .schemas import ChatMessage


def content_text(content: Optional[Union[str, List[Any]]]) -> str:
    """Extract plain text from a message's content (string or content-parts)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        if isinstance(part, dict):
            if part.get("type") == "text":
                parts.append(part.get("text", ""))
        else:
            parts.append(str(part))
    return "\n".join(p for p in parts if p)


def messages_to_prompt(messages: List[ChatMessage]) -> str:
    """Flatten an OpenAI ``messages`` array into a single Copilot prompt.

    Copilot's protocol has no role/system channel — it takes one prompt string per
    turn — so we collapse the whole conversation into one piece of text.

    To avoid the upstream ``text-too-long`` error, we limit the total prompt length
    and drop oldest turns when the conversation is too long.
    """
    SYSTEM_MAX = 1024        # system prompt cap
    BODY_MAX = 6000          # per-turn body cap (keeps total under ~8k)
    MAX_TURNS_IN_HISTORY = 6 # keep last N user/assistant turns max

    system = "\n\n".join(
        content_text(m.content) for m in messages if m.role == "system" and m.content
    )[:SYSTEM_MAX]
    convo = [m for m in messages if m.role != "system"]

    # Keep only the last MAX_TURNS_IN_HISTORY conversation turns to avoid
    # the upstream "text-too-long" error on long threads.
    if len(convo) > MAX_TURNS_IN_HISTORY:
        convo = convo[-MAX_TURNS_IN_HISTORY:]

    if len(convo) == 1 and convo[0].role == "user":
        body = content_text(convo[0].content)[:BODY_MAX]
    else:
        lines = []
        for m in convo:
            label = "User" if m.role == "user" else "Assistant"
            lines.append(f"{label}: {content_text(m.content)[:BODY_MAX]}")
        lines.append("Assistant:")  # cue Copilot to continue
        body = "\n".join(lines)

    if system and body:
        return f"{system}\n\n{body}"
    return system or body
