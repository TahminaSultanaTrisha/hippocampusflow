"""One thin wrapper around the Anthropic SDK.

Everything AI-related goes through these two functions, which means:
- the API key is read in exactly one place,
- tests can fake the AI by monkeypatching two functions,
- retries/logging can be added here later without touching agents.
"""
import base64
import json

import anthropic

from app.core.config import get_settings

_MEDIA_BY_EXT = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


def image_block(data: bytes, ext: str) -> dict:
    """Package raw image bytes the way the Messages API expects."""
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _MEDIA_BY_EXT.get(ext, "image/jpeg"),
            "data": base64.b64encode(data).decode(),
        },
    }


def _client() -> anthropic.Anthropic:
    key = get_settings().anthropic_api_key
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env -- see README."
        )
    return anthropic.Anthropic(api_key=key)


def complete_text(model: str, system: str, content: list) -> str:
    """Send one user turn (text and/or image blocks); return the text reply."""
    message = _client().messages.create(
        model=model, max_tokens=1024, system=system,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def complete_json(model: str, system: str, content: list) -> dict:
    """Same, but the prompt demands JSON; parse it (with fence-stripping)."""
    text = complete_text(model, system, content).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def chat_text(model: str, system: str, messages: list[dict]) -> str:
    """Multi-turn conversation; returns the assistant's text reply."""
    message = _client().messages.create(
        model=model, max_tokens=1024, system=system, messages=messages,
    )
    return "".join(block.text for block in message.content if block.type == "text")
