"""The installed OpenAI SDK still offers every call Comic Chaos makes.

Checked by signature only; nothing is sent. Narratron silently falls back
when Structured Outputs fail, so an SDK change would otherwise go unnoticed.
"""

import inspect

from openai import OpenAI


def test_sdk_supports_the_calls_we_make(api_key):
    client = OpenAI(api_key=api_key)

    chat = inspect.signature(client.chat.completions.create).parameters
    assert {"model", "messages", "temperature", "top_p", "max_tokens", "response_format"} <= chat.keys()
    assert callable(client.beta.chat.completions.parse)  # Structured Outputs path

    images = inspect.signature(client.images.generate).parameters
    assert {"model", "prompt", "size", "quality", "moderation", "stream", "partial_images"} <= images.keys()
