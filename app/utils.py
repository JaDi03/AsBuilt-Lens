"""
AsBuilt Lens — Utility Functions
Visual annotations, formatting, color management, and UI helpers.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional, Tuple


# ─── Color Palette ─────────────────────────────────────────────────────

COLORS = {
    "present": {
        "primary": "#10B981",      # Emerald green
        "bg": "#D1FAE5",           # Light green background
        "text": "#065F46",         # Dark green text
        "label": "PASS"
    },
    "missing": {
        "primary": "#ED1C24",      # AMD Red
        "bg": "#FEE2E2",           # Light red background
        "text": "#991B1B",         # Dark red text
        "label": "MISSING"
    },
    "anomaly": {
        "primary": "#F59E0B",      # Amber/warning
        "bg": "#FEF3C7",           # Light amber background
        "text": "#92400E",         # Dark amber text
        "label": "ANOMALY"
    },
    "unexpected": {
        "primary": "#8B5CF6",      # Purple
        "bg": "#EDE9FE",           # Light purple background
        "text": "#5B21B6",         # Dark purple text
        "label": "UNEXPECTED"
    }
}

STATUS_ICONS = {
    "present": "✅",
    "missing": "❌",
    "anomaly": "⚠️",
    "unexpected": "🟣"
}


# ─── Image Annotations ────────────────────────────────────────────────

def annotate_image(image: Image.Image, items: List[Dict]) -> Image.Image:
    """
    Draw visual annotations on the inspection image.
    Shows item labels with status colors in a corner overlay.
    """
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Try to load a nice font, fall back to default
    try:
        font_size = max(14, min(width, height) // 40)
        font = ImageFont.truetype("arial.ttf", font_size)
        font_small = ImageFont.truetype("arial.ttf", max(11, font_size - 4))
    except (IOError, OSError):
        font = ImageFont.load_default()
        font_small = font
        font_size = 12

    # Draw semi-transparent overlay panel on top-left
    padding = 12
    line_height = font_size + 10
    panel_height = padding * 2 + line_height * (len(items) + 1) + 8
    panel_width = min(width - 20, max(280, width // 3))

    # Create overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Draw panel background (Using a clean dark theme for contrast over image)
    overlay_draw.rounded_rectangle(
        [10, 10, 10 + panel_width, 10 + panel_height],
        radius=12,
        fill=(15, 23, 42, 200)  # Dark slate with transparency
    )

    # Convert to RGBA for blending
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Draw header
    y_pos = padding + 10
    draw.text((padding + 14, y_pos), "🔍 Inspection Results", fill="white", font=font)
    y_pos += line_height + 4

    # Draw separator line
    draw.line([(padding + 14, y_pos), (10 + panel_width - padding, y_pos)],
              fill=(100, 116, 139), width=1)
    y_pos += 8

    # Draw each item
    for item in items:
        status = item.get("status", "present")
        icon = STATUS_ICONS.get(status, "❓")
        color_info = COLORS.get(status, COLORS["present"])
        name = item.get("id", "unknown").replace("_", " ").title()
        count_info = f"{item.get('detected_count', '?')}/{item.get('expected_count', '?')}"
        confidence = item.get("confidence", 0)

        label = f"{icon} {name}: {count_info}"
        if confidence > 0:
            label += f" ({confidence}%)"

        draw.text((padding + 14, y_pos), label, fill=color_info["primary"], font=font_small)
        y_pos += line_height

    # Convert back to RGB for Streamlit display
    img = img.convert("RGB")
    return img


def draw_inspection_badge(image: Image.Image, passed: bool) -> Image.Image:
    """
    Draw a large PASS/FAIL badge on the top-right corner of the image.
    """
    img = image.copy()

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size
    badge_w = min(160, width // 4)
    badge_h = min(50, height // 10)

    x = width - badge_w - 15
    y = 15

    if passed:
        bg_color = (16, 185, 129, 220)    # Emerald green
        text = "✅ PASS"
    else:
        bg_color = (237, 28, 36, 220)     # AMD Red
        text = "❌ FAIL"

    draw.rounded_rectangle([x, y, x + badge_w, y + badge_h], radius=10, fill=bg_color)

    try:
        font = ImageFont.truetype("arial.ttf", max(16, badge_h // 2))
    except (IOError, OSError):
        font = ImageFont.load_default()

    # Center text in badge
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = x + (badge_w - text_w) // 2
    text_y = y + (badge_h - text_h) // 2

    draw.text((text_x, text_y), text, fill="white", font=font)

    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


# ─── Result Formatting ─────────────────────────────────────────────────

def format_elapsed_time(seconds: float) -> str:
    """Format elapsed time for display."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def get_status_color(status: str) -> str:
    """Get the primary color hex code for a given status."""
    return COLORS.get(status, COLORS["present"])["primary"]


def get_status_icon(status: str) -> str:
    """Get the emoji icon for a given status."""
    return STATUS_ICONS.get(status, "❓")


def get_status_bg_color(status: str) -> str:
    """Get the background color hex code for a given status."""
    return COLORS.get(status, COLORS["present"])["bg"]


def calculate_pass_rate(items: List[Dict]) -> Tuple[int, int]:
    """Calculate the number of passed items vs total items."""
    total = len(items)
    passed = sum(1 for item in items if item.get("status") == "present")
    return passed, total


def format_confidence_bar(confidence: int, width: int = 20) -> str:
    """Create a text-based confidence bar for terminal/log display."""
    filled = int((confidence / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {confidence}%"


# ─── Inspection History ────────────────────────────────────────────────

def create_history_entry(
    image: Image.Image,
    result: Dict,
    elapsed: float,
    specification: str
) -> Dict:
    """
    Create a history entry for the session history panel.
    """
    # Create thumbnail
    thumb_size = (120, 120)
    thumbnail = image.copy()
    thumbnail.thumbnail(thumb_size, Image.LANCZOS)

    passed, total = calculate_pass_rate(result.get("items", []))

    return {
        "thumbnail": thumbnail,
        "passed": result.get("inspection_passed", False),
        "passed_count": passed,
        "total_count": total,
        "elapsed": elapsed,
        "summary": result.get("summary", ""),
        "specification": specification[:100] + "..." if len(specification) > 100 else specification,
        "timestamp": __import__("datetime").datetime.now().strftime("%H:%M:%S"),
    }
