"""Synthetic images and SSE helpers for tests."""

import json
from io import BytesIO

from PIL import Image, ImageDraw

# A speech bubble drawn by make_bubble_png (x, y, width, height)
BUBBLE_BOX = (300, 200, 400, 300)
NARRATION_BOX = (100, 100, 700, 220)


def make_bubble_png(size: int = 1024) -> bytes:
    """A dark panel with one large, empty, outlined white oval (a speech bubble)."""
    img = Image.new("RGB", (size, size), (40, 60, 90))
    x, y, w, h = BUBBLE_BOX
    ImageDraw.Draw(img).ellipse([x, y, x + w, y + h], fill="white", outline="black", width=6)
    return _png(img)


def make_narration_png(size: int = 1024) -> bytes:
    """A dark panel with one large, empty, outlined white rectangle (a narration box)."""
    img = Image.new("RGB", (size, size), (90, 40, 40))
    x, y, w, h = NARRATION_BOX
    ImageDraw.Draw(img).rectangle([x, y, x + w, y + h], fill="white", outline="black", width=6)
    return _png(img)


def _png(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def parse_sse(body: bytes) -> list[dict]:
    """Decode a text/event-stream body into its JSON events."""
    events = []
    for line in body.decode("utf-8").splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: "):]))
    return events
