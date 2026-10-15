"""Bubble detection, text rendering, and strip assembly on synthetic images."""

from io import BytesIO

from PIL import Image

from src.comic_strip import ComicStrip
from src.image_gen.panel_detector import PanelDetector
from src.image_gen.text_renderer import TextElement, TextRenderer
from helpers import BUBBLE_BOX, NARRATION_BOX, make_bubble_png, make_narration_png


def roughly(actual, expected, tolerance=15):
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def test_detects_speech_bubble():
    bubbles = PanelDetector().detect_bubbles(make_bubble_png())
    assert len(bubbles) == 1
    b = bubbles[0]
    assert roughly((b.x, b.y, b.width, b.height), BUBBLE_BOX)


def test_detects_narration_box():
    boxes = PanelDetector().detect_narration_boxes(make_narration_png())
    assert len(boxes) == 1
    b = boxes[0]
    assert roughly((b.x, b.y, b.width, b.height), NARRATION_BOX)


def test_no_regions_in_empty_or_invalid_images():
    detector = PanelDetector()
    blank = Image.new("RGB", (1024, 1024), (30, 30, 30))
    buf = BytesIO()
    blank.save(buf, format="PNG")
    assert detector.detect_bubbles(buf.getvalue()) == []
    assert detector.detect_bubbles(b"not an image") == []


def test_text_is_rendered_inside_the_bubble():
    png = make_bubble_png()
    bubble = PanelDetector().detect_bubbles(png)[0]
    before = Image.open(BytesIO(png)).convert("RGB")

    after = TextRenderer().render_text_on_image(before.copy(), bubble, TextElement("Hei på deg!", "speech"))

    assert after.size == before.size
    x, y, w, h = BUBBLE_BOX
    inside = (x + w // 4, y + h // 4, x + 3 * w // 4, y + 3 * h // 4)
    assert after.crop(inside).getextrema() != before.crop(inside).getextrema()  # text drawn
    outside = (0, 0, 200, 150)
    assert after.crop(outside).tobytes() == before.crop(outside).tobytes()  # scene untouched


def test_strip_assembly():
    strip = ComicStrip(title="Test")
    speech = [{"type": "speech", "user_input": True, "position": "top-left"}]
    strip.add_panel(make_bubble_png(), "title", 0)
    strip.add_panel(make_bubble_png(), "p1", 1, elements=speech, user_input_text="Hello!")
    strip.add_panel(make_narration_png(), "p2", 2,
                    elements=[{"type": "narration", "user_input": False, "text": "Later..."}])
    strip.add_panel(None, "missing image", 3)  # panels without an image are skipped

    image = Image.open(BytesIO(strip.generate_comic_strip()))
    assert image.format == "PNG"
    assert image.width > image.height  # three panels fit on one row


def test_empty_strip_returns_none():
    assert ComicStrip().generate_comic_strip() is None
