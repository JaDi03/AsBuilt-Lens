"""
AsBuilt Lens — Quality Engineer Agent
Triggered when an inspection fails. Analyzes the failure root cause and suggests corrective actions.
"""

import json
import time
import logging
from PIL import Image
from inspector import call_vlm, prepare_image, parse_vlm_response
from config import VLM_MAX_RETRIES, VLM_RETRY_DELAY

logger = logging.getLogger(__name__)

QE_PROMPT_TEMPLATE = """
You are a Senior Industrial Quality Engineer Agent. The Visual Inspector Agent has just flagged a failure on the assembly line.
Here is the raw data from the Inspector Agent:
{inspection_json}

Your job is to analyze the original image alongside the Inspector's findings.
Focus specifically on items marked as "missing", "anomaly", or "unexpected".

Determine the Root Cause of the failure based on the visual evidence.
Provide a detailed Corrective Action Plan.

Return ONLY a valid JSON object with the following format. No markdown, no extra text:
{
  "root_cause_analysis": "Detailed explanation of the likely physical or process failure.",
  "severity": "CRITICAL, MAJOR, or MINOR",
  "corrective_actions": ["Action 1", "Action 2"],
  "preventive_measures": ["Measure 1", "Measure 2"]
}
"""

def run_quality_engineer_agent(image: Image.Image, inspector_result: dict) -> dict:
    """
    Agentic handoff: Takes the failed inspection data and the original image,
    and performs a deeper root cause analysis.
    """
    start_time = time.time()
    
    try:
        image_b64 = prepare_image(image)
    except Exception as e:
        logger.error(f"[QUALITY ENGINEER] Image prep failed: {e}")
        return {"error": str(e)}

    # Inject the previous agent's findings into the prompt
    # Strip out boxes_2d to save tokens, as the QE agent doesn't need to see the exact coordinates to know what failed
    clean_result = {"inspection_passed": inspector_result.get("inspection_passed")}
    clean_items = []
    for item in inspector_result.get("items", []):
        i = item.copy()
        if "boxes_2d" in i:
            del i["boxes_2d"]
        clean_items.append(i)
    clean_result["items"] = clean_items

    prompt = QE_PROMPT_TEMPLATE.replace("{inspection_json}", json.dumps(clean_result, indent=2))
    
    last_error = None
    for attempt in range(VLM_MAX_RETRIES):
        try:
            logger.info(f"[QUALITY ENGINEER] Analyzing root cause (Attempt {attempt + 1})")
            raw_response = call_vlm(image_b64, prompt)
            qe_result = parse_vlm_response(raw_response)
            
            # Ensure fields exist
            qe_result.setdefault("root_cause_analysis", "Unable to determine root cause.")
            qe_result.setdefault("severity", "MAJOR")
            qe_result.setdefault("corrective_actions", ["Manual review required"])
            qe_result.setdefault("preventive_measures", ["Review process controls"])
            
            elapsed = time.time() - start_time
            logger.info(f"[QUALITY ENGINEER] Analysis complete in {elapsed:.1f}s")
            
            return {
                "result": qe_result,
                "elapsed": elapsed,
                "error": None
            }
            
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[QUALITY ENGINEER] Error on attempt {attempt + 1}: {e}")
            if attempt < VLM_MAX_RETRIES - 1:
                time.sleep(VLM_RETRY_DELAY * (2 ** attempt))

    return {
        "result": None,
        "elapsed": time.time() - start_time,
        "error": f"Quality Engineer Agent failed after {VLM_MAX_RETRIES} attempts. Last error: {last_error}"
    }
