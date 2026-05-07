"""
AsBuilt Lens — Configuration Module
Loads environment variables and defines application constants.
"""

import os
from dotenv import load_dotenv

# Load .env from project root relative to this file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=True)

# ─── AMD Developer Cloud ───────────────────────────────────────────────
AMD_API_URL = os.getenv("AMD_API_URL", "http://localhost:8000/v1")
AMD_API_KEY = os.getenv("AMD_API_KEY", "")
VLM_MODEL = os.getenv("VLM_MODEL", "Qwen/Qwen3-VL-32B-Instruct")

# ─── Camera ────────────────────────────────────────────────────────────
CAMERA_URL = os.getenv("CAMERA_URL", "http://192.168.1.100:4747/video")
CAMERA_SOURCE_LOCAL = int(os.getenv("CAMERA_SOURCE_LOCAL", "0"))  # Ensure it is an integer

# ─── Stability Detection ──────────────────────────────────────────────
STABILITY_THRESHOLD = float(os.getenv("STABILITY_THRESHOLD", "0.02"))
STABILITY_FRAMES = int(os.getenv("STABILITY_FRAMES", "30"))

# ─── Image Processing ─────────────────────────────────────────────────
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "640"))
CAPTURE_RESOLUTION = (640, 480)
SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp"]

# ─── VLM Configuration ────────────────────────────────────────────────
VLM_MAX_TOKENS = 2048
VLM_TEMPERATURE = 0.1
VLM_TIMEOUT = 60  # seconds
VLM_MAX_RETRIES = 3
VLM_RETRY_DELAY = 2  # seconds (base for exponential backoff)

# ─── Inspection Templates ─────────────────────────────────────────────
INSPECTION_TEMPLATES = {
    "Custom Specification": "",
    "PCB Assembly": """Expected items:
- 4x resistor (small rectangular components, through-hole)
- 1x electrolytic capacitor (cylindrical, vertical mount)
- 1x IC chip (black, rectangular, with visible pins)
- 1x LED (small dome-shaped component)""",

    "Packaging Verification": """Expected items:
- 1x product unit (main item in packaging)
- 1x user manual or instruction sheet (printed paper)
- 1x warranty card
- 1x power adapter or cable
- 1x protective foam or bubble wrap""",

    "Tool Kit Inspection": """Expected items:
- 1x Phillips head screwdriver
- 1x flat head screwdriver
- 1x adjustable wrench
- 1x needle-nose pliers
- 1x wire cutter
- 1x tape measure
- 1x utility knife""",

    "Electrical Panel": """Expected items:
- 1x Main circuit breaker (Large unit at the top, GACIA MM1)
- 5x Double-pole circuit breakers (Wider blue/white units, CHINT brand)
- 3x Single-pole circuit breakers (Narrower blue/white units, CHINT brand)
- 1x Warning sign (Yellow triangle with lightning bolt icon)
- 1x Voltage label (Yellow rectangle with '220 VOLTIOS' text)
- 2x Terminal blocks (Grey units next to the small breakers)
- 2x Ground/Neutral bars (Vertical metallic strips on left and right sides)""",

    "BGS Tool Kit": """Expected items:
- 4x Screwdrivers (Top right, black and red handles)
- 6x Open-end wrenches (Bottom right, arranged by size)
- 1x Hammer (Center position, red head)
- 2x Pliers (Bottom left, red and yellow handles)
- 1x T-handle wrench (Top left, large red tool)
- 9x Sockets (Far left column, red finish)
- 1x Retractable Cutter/Utility Knife (Center right, thick black and red body, positioned vertically)"""
}

# ─── UI Configuration ─────────────────────────────────────────────────
APP_TITLE = "AsBuilt Lens"
APP_ICON = "🔍"
APP_TAGLINE = "Describe what should exist, the AI verifies it visually."
APP_VERSION = "1.0.0"
