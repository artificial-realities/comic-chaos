"""Text cleaning for user input and model output.

Removes null bytes, invisible and control characters, and normalizes Unicode,
so neither the reader's text nor the model's can corrupt later prompts or the
rendered strip.
"""

import re
import unicodedata
from typing import Any

# Null bytes
_NULL_BYTE_PATTERN = re.compile(r"\x00")

# Zero-width and invisible Unicode characters that should not appear in comic text
_INVISIBLE_CHARS = re.compile(
    r"[​‌‍‎‏"  # zero-width spaces/joiners/marks
    r"‪-‮"  # bidi control
    r"﻿"  # BOM
    r"￼"  # object replacement character
    r"￾￿"  # noncharacters
    r"]"
)


def sanitize_text(text: str) -> str:
    """Sanitize a single text string for encoding integrity.

    Removes null bytes, invisible characters, and normalizes Unicode.
    Preserves all valid content including Norwegian characters (æ, ø, å),
    accented letters, and symbols like €.

    This function is idempotent: calling it on already-clean text
    returns the same text unchanged.

    Args:
        text: The string to sanitize.

    Returns:
        The sanitized string.
    """
    if not text:
        return text

    # 1. Remove null bytes
    text = _NULL_BYTE_PATTERN.sub("", text)

    # 2. Remove invisible/control characters (except normal whitespace)
    text = _INVISIBLE_CHARS.sub("", text)

    # 3. Remove other C0/C1 control characters except tab, newline, carriage return
    text = "".join(
        ch for ch in text
        if ch in ("\t", "\n", "\r") or unicodedata.category(ch) != "Cc"
    )

    # 4. Normalize Unicode to NFC (composed form) — this ensures that
    # characters like å (U+00E5) aren't split into a + combining ring
    text = unicodedata.normalize("NFC", text)

    return text


def sanitize_parsed_response(data: Any) -> Any:
    """Deep-clean all string values in a parsed JSON structure.

    Recursively walks dicts and lists, applying sanitize_text() to
    every string value. Non-string values are passed through unchanged.

    Args:
        data: A parsed JSON structure (dict, list, str, int, float, bool, None).

    Returns:
        The same structure with all strings sanitized.
    """
    if isinstance(data, str):
        return sanitize_text(data)
    elif isinstance(data, dict):
        return {k: sanitize_parsed_response(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_parsed_response(item) for item in data]
    else:
        return data
