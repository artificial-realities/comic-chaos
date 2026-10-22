"""The installed OpenAI SDK still offers every call Comic Chaos makes.

Checked by signature only; nothing is sent. Narratron falls back to a safe
panel when a call fails, so an SDK change would otherwise only show in the log.
"""

import inspect

from openai import OpenAI


def test_sdk_supports_the_calls_we_make(api_key):
    client = OpenAI(api_key=api_key)

    chat = inspect.signature(client.chat.completions.parse).parameters
    assert {"model", "messages", "temperature", "top_p", "max_tokens", "response_format"} <= chat.keys()

    images = inspect.signature(client.images.generate).parameters
    assert {"model", "prompt", "size", "quality", "moderation", "stream", "partial_images"} <= images.keys()
