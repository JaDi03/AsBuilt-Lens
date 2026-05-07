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
        "primary": "#E8640A",      # AMD Orange (Better contrast on Green PCB)
        "bg": "#FFF7ED",           # Light orange background
        "text": "#7C2D12",         # Dark orange text
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
    "present": "[PASS]",
    "missing": "[FAIL]",
    "anomaly": "[WARN]",
    "unexpected": "[UNEX]"
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

    # Draw each item
    padding = 12
    y_pos = padding + 10

    # Draw each item
    for item in items:
        status = item.get("status", "present")
        icon = STATUS_ICONS.get(status, "❓")
        color_info = COLORS.get(status, COLORS["present"])
        name = item.get("id", "unknown").replace("_", " ").title()
        count_info = f"{item.get('detected_count', '?')}/{item.get('expected_count', '?')}"
        confidence = item.get("confidence", 0)

        # ── Draw Bounding Boxes ──
        boxes = item.get("boxes_2d", [])
        
        # Robust parsing: ensure we have a list of lists
        if boxes and isinstance(boxes, list):
            # If it's a single flat list [y,x,y,x], wrap it
            if len(boxes) == 4 and all(isinstance(x, (int, float)) for x in boxes):
                boxes = [boxes]
            
            for box in boxes:
                try:
                    if not isinstance(box, list) or len(box) < 4:
                        continue
                        
                    # Qwen3-VL returns [ymin, xmin, ymax, xmax]
                    # Swapping based on previous visual feedback: left=ymin, top=xmin
                    ymin, xmin, ymax, xmax = box[:4]
                    
                    left = ymin * width / 1000
                    top = xmin * height / 1000
                    right = ymax * width / 1000
                    bottom = xmax * height / 1000
                except (ValueError, TypeError):
                    continue # Skip malformed boxes

                # Draw glowing box
                for i in range(3): # Multi-layered border for glow effect
                    draw.rectangle(
                        [left - i, top - i, right + i, bottom + i],
                        outline=color_info["primary"],
                        width=2
                    )
                
                # Small ID label with background for high contrast
                label_text = name
                t_bbox = draw.textbbox((left, top), label_text, font=font_small)
                # Draw a small background rectangle for the text
                draw.rectangle([t_bbox[0]-2, t_bbox[1]-2, t_bbox[2]+2, t_bbox[3]+2], fill=color_info["primary"])
                draw.text((left, top-2), label_text, fill="white", font=font_small)

        # Bounding boxes were drawn above. No text list here.
        pass


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
        text = "PASS"
    else:
        bg_color = (237, 28, 36, 220)     # AMD Red
        text = "FAIL"

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
    annotated_image: Image.Image,
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
        "annotated_image": annotated_image,
        "original_image": image,
        "result": result,
        "passed": result.get("inspection_passed", False),
        "passed_count": passed,
        "total_count": total,
        "elapsed": elapsed,
        "usage": result.get("usage", {}),
        "summary": result.get("summary", ""),
        "full_specification": specification,
        "specification_short": specification[:100] + "..." if len(specification) > 100 else specification,
        "timestamp": __import__("datetime").datetime.now().strftime("%H:%M:%S"),
    }
