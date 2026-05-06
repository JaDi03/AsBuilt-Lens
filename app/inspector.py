"""
AsBuilt Lens — Inspector Module
Handles VLM calls to AMD Developer Cloud and JSON response parsing.
Uses OpenAI-compatible API format (vLLM endpoint on MI300X).
"""

import json
import time
import base64
import logging
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image

from config import (
    AMD_API_URL, AMD_API_KEY, VLM_MODEL,
    VLM_MAX_TOKENS, VLM_TEMPERATURE, VLM_TIMEOUT,
    VLM_MAX_RETRIES, VLM_RETRY_DELAY, MAX_IMAGE_SIZE
)

logger = logging.getLogger(__name__)

# ─── Prompt Loading ────────────────────────────────────────────────────

PROMPT_PATH = Path(__file__).parent / "prompts" / "inspection_prompt.txt"


def load_prompt_template() -> str:
    """Load the structured inspection prompt template from file."""
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"Prompt template not found at {PROMPT_PATH}")
        raise


def build_prompt(specification: str) -> str:
    """Build the full prompt by injecting the user's specification."""
    template = load_prompt_template()
    return template.replace("{specification}", specification)


# ─── Image Processing ──────────────────────────────────────────────────

def prepare_image(image: Image.Image, max_size: int = MAX_IMAGE_SIZE) -> str:
    """
    Resize image to max dimension and convert to base64 JPEG.
    Returns base64-encoded string ready for API call.
    """
    # Resize maintaining aspect ratio
    width, height = image.size
    if max(width, height) > max_size:
        ratio = max_size / max(width, height)
        new_size = (int(width * ratio), int(height * ratio))
        image = image.resize(new_size, Image.LANCZOS)

    # Convert to RGB if necessary (handle RGBA, palette, etc.)
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Encode as JPEG base64
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


# ─── VLM API Call ──────────────────────────────────────────────────────

def call_vlm(image_b64: str, prompt: str) -> dict:
    """
    Send image + prompt to VLM endpoint (OpenAI-compatible format).
    Returns the raw API response dict.
    """
    headers = {
        "Content-Type": "application/json",
    }
    if AMD_API_KEY:
        headers["Authorization"] = f"Bearer {AMD_API_KEY}"

    payload = {
        "model": VLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": VLM_MAX_TOKENS,
        "temperature": VLM_TEMPERATURE,
    }

    url = f"{AMD_API_URL}/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=VLM_TIMEOUT)
    response.raise_for_status()
    return response.json()


# ─── JSON Parsing ──────────────────────────────────────────────────────

def parse_vlm_response(response: dict) -> dict:
    """
    Extract and parse JSON from the VLM response.
    Handles potential markdown fences and trailing text.
    """
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error(f"Unexpected response structure: {e}")
        raise ValueError(f"Invalid VLM response structure: {e}")

    # Clean markdown fences if present
    clean_text = content.strip()
    if clean_text.startswith("```"):
        # Remove starting ```json or ```
        clean_text = clean_text.split("\n", 1)[-1]
        # Remove ending ```
        if clean_text.endswith("```"):
            clean_text = clean_text.rsplit("```", 1)[0]
    
    # Try to find the first '{' and last '}' in case there is garbage text
    try:
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            json_str = clean_text[start_idx:end_idx + 1]
            return json.loads(json_str)
        
        # If no braces found, try direct load
        return json.loads(clean_text)
    except Exception as e:
        logger.error(f"Failed to parse JSON from VLM response: {content[:500]}")
        raise ValueError(f"Failed to parse JSON: {str(e)}")


def validate_result(result: dict) -> dict:
    """
    Validate and normalize the inspection result structure.
    Fills in missing fields with defaults.
    """
    # Ensure required top-level fields
    if "inspection_passed" not in result:
        result["inspection_passed"] = False

    if "items" not in result:
        result["items"] = []

    if "summary" not in result:
        result["summary"] = "Inspection completed — no summary provided by model."

    if "notes" not in result:
        result["notes"] = ""

    # Validate each item
    for item in result["items"]:
        item.setdefault("id", "unknown_item")
        item.setdefault("expected_count", 0)
        item.setdefault("detected_count", 0)
        item.setdefault("status", "present")
        item.setdefault("confidence", 50)
        item.setdefault("note", "")

        # Clamp confidence to 0-100
        item["confidence"] = max(0, min(100, int(item.get("confidence", 50))))

        # Ensure status is valid
        valid_statuses = {"present", "missing", "anomaly", "unexpected"}
        if item["status"] not in valid_statuses:
            item["status"] = "anomaly"

    return result


# ─── Main Inspection Function ─────────────────────────────────────────

def run_inspection(image: Image.Image, specification: str) -> dict:
    """
    Run a complete inspection cycle:
    1. Prepare image (resize + base64)
    2. Build prompt with specification
    3. Call VLM with retry logic
    4. Parse and validate JSON response

    Returns dict with:
        - result: parsed inspection JSON
        - elapsed: time in seconds
        - error: error message if failed, None if success
    """
    start_time = time.time()

    # Prepare image
    try:
        image_b64 = prepare_image(image)
    except Exception as e:
        return {
            "result": None,
            "elapsed": time.time() - start_time,
            "error": f"Image processing failed: {str(e)}"
        }

    # Build prompt
    prompt = build_prompt(specification)

    # Call VLM with retry logic
    last_error = None
    for attempt in range(VLM_MAX_RETRIES):
        try:
            logger.info(f"VLM call attempt {attempt + 1}/{VLM_MAX_RETRIES}")
            raw_response = call_vlm(image_b64, prompt)
            result = parse_vlm_response(raw_response)
            result = validate_result(result)

            elapsed = time.time() - start_time
            logger.info(f"Inspection completed in {elapsed:.1f}s")

            return {
                "result": result,
                "elapsed": elapsed,
                "error": None
            }

        except requests.exceptions.Timeout:
            last_error = "Connection to AMD Cloud timed out. The server may be busy."
            logger.warning(f"Timeout on attempt {attempt + 1}")

        except requests.exceptions.ConnectionError:
            last_error = "Cannot connect to AMD Cloud. Please check your endpoint URL and network."
            logger.warning(f"Connection error on attempt {attempt + 1}")

        except requests.exceptions.HTTPError as e:
            last_error = f"AMD Cloud returned an error: {e.response.status_code} — {e.response.text[:200]}"
            logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")

        except ValueError as e:
            last_error = f"Failed to parse VLM response: {str(e)}"
            logger.warning(f"Parse error on attempt {attempt + 1}: {e}")

        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")

        # Exponential backoff before retry
        if attempt < VLM_MAX_RETRIES - 1:
            delay = VLM_RETRY_DELAY * (2 ** attempt)
            logger.info(f"Retrying in {delay}s...")
            time.sleep(delay)

    elapsed = time.time() - start_time
    return {
        "result": None,
        "elapsed": elapsed,
        "error": f"All {VLM_MAX_RETRIES} attempts failed. Last error: {last_error}"
    }


def run_discovery(image: Image.Image) -> dict:
    """
    Experimental 'Discovery Mode' to identify all visible components.
    Returns a descriptive list of what the VLM sees.
    """
    prompt = (
        "Identify every physical component visible in this image. "
        "For each item, provide a clear name and a very brief description of its appearance. "
        "Also include its bounding box coordinates [ymin, xmin, ymax, xmax] normalized to 1000. "
        "Return ONLY a JSON object with a list of 'discovered_items'."
    )
    
    start_time = time.time()
    try:
        image_b64 = prepare_image(image)
        raw_response = call_vlm(image_b64, prompt)
        result = parse_vlm_response(raw_response)
        
        return {
            "result": result,
            "elapsed": time.time() - start_time,
            "error": None
        }
    except Exception as e:
        return {
            "result": None,
            "elapsed": time.time() - start_time,
            "error": str(e)
        }


# ─── Mock Inspection (for offline development) ────────────────────────

def run_mock_inspection(image: Image.Image, specification: str) -> dict:
    """
    Mock inspection for development without AMD Cloud connection.
    Returns a realistic-looking result for UI testing.
    """
    import random
    time.sleep(random.uniform(1.5, 3.0))  # Simulate API latency

    mock_result = {
        "inspection_passed": random.choice([True, False]),
        "items": [
            {
                "id": "resistor",
                "expected_count": 4,
                "detected_count": random.choice([3, 4]),
                "status": "present" if random.random() > 0.3 else "anomaly",
                "confidence": random.randint(75, 98),
                "note": ""
            },
            {
                "id": "capacitor",
                "expected_count": 1,
                "detected_count": random.choice([0, 1]),
                "status": random.choice(["present", "missing"]),
                "confidence": random.randint(70, 95),
                "note": ""
            },
            {
                "id": "ic_chip",
                "expected_count": 1,
                "detected_count": 1,
                "status": "present",
                "confidence": random.randint(85, 99),
                "note": ""
            },
            {
                "id": "led",
                "expected_count": 1,
                "detected_count": 1,
                "status": "present",
                "confidence": random.randint(80, 96),
                "note": ""
            }
        ],
        "summary": "",
        "notes": "Mock inspection — connect to AMD Cloud for real analysis."
    }

    # Fix consistency
    passed_items = sum(1 for item in mock_result["items"] if item["status"] == "present")
    total_items = len(mock_result["items"])
    mock_result["inspection_passed"] = passed_items == total_items
    mock_result["summary"] = f"{passed_items} of {total_items} items verified correctly."

    for item in mock_result["items"]:
        if item["status"] == "missing":
            item["detected_count"] = 0
            item["note"] = f"No {item['id']} visible in expected location."
        elif item["status"] == "anomaly":
            item["note"] = f"Count mismatch for {item['id']}."

    return {
        "result": mock_result,
        "elapsed": random.uniform(2.0, 4.5),
        "error": None
    }
