"""
AsBuilt Lens — Inspection Report Generator
Generates professional HTML inspection reports for download.
Provides a tangible, shareable output from each inspection run.
"""

import base64
import io
from datetime import datetime
from PIL import Image
from typing import Dict, List, Optional


def _encode_image_to_base64(image: Image.Image, max_width: int = 800) -> str:
    """Resize and encode a PIL image to base64 JPEG for embedding in HTML."""
    width, height = image.size
    if width > max_width:
        ratio = max_width / width
        image = image.resize((max_width, int(height * ratio)), Image.LANCZOS)
    
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _get_status_color(status: str) -> str:
    """Get the hex color for a given status."""
    colors = {
        "present": "#10B981",
        "missing": "#ED1C24",
        "anomaly": "#F59E0B",
        "unexpected": "#8B5CF6",
    }
    return colors.get(status, "#8B919A")


def _get_status_label(status: str) -> str:
    """Get the display label for a given status."""
    labels = {
        "present": "✅ PRESENT",
        "missing": "❌ MISSING",
        "anomaly": "⚠️ ANOMALY",
        "unexpected": "🟣 UNEXPECTED",
    }
    return labels.get(status, "❓ UNKNOWN")


def generate_inspection_report(
    result: Dict,
    specification: str,
    elapsed: float,
    original_image: Optional[Image.Image] = None,
    annotated_image: Optional[Image.Image] = None,
) -> str:
    """
    Generate a self-contained HTML inspection report.
    
    Args:
        result: Parsed inspection result dict with items, summary, etc.
        specification: The original inspection specification text.
        elapsed: Elapsed time in seconds.
        original_image: The original captured/uploaded image.
        annotated_image: The annotated image with bounding boxes and badge.
    
    Returns:
        Complete HTML string ready for download.
    """
    # Extract data
    passed = result.get("inspection_passed", False)
    items = result.get("items", [])
    summary = result.get("summary", "No summary available.")
    notes = result.get("notes", "")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_display = datetime.now().strftime("%B %d, %Y at %H:%M")
    
    # Calculate stats
    total_items = len(items)
    passed_items = sum(1 for i in items if i.get("status") == "present")
    missing_items = sum(1 for i in items if i.get("status") == "missing")
    anomaly_items = sum(1 for i in items if i.get("status") == "anomaly")
    avg_confidence = (
        sum(i.get("confidence", 0) for i in items) / total_items
        if total_items > 0
        else 0
    )
    
    # Format elapsed time
    if elapsed < 1:
        elapsed_str = f"{elapsed * 1000:.0f}ms"
    elif elapsed < 60:
        elapsed_str = f"{elapsed:.1f}s"
    else:
        mins = int(elapsed // 60)
        secs = elapsed % 60
        elapsed_str = f"{mins}m {secs:.1f}s"
    
    # Verdict styling
    verdict_color = "#10B981" if passed else "#ED1C24"
    verdict_text = "PASSED" if passed else "FAILED"
    verdict_bg = "rgba(16, 185, 129, 0.15)" if passed else "rgba(237, 28, 36, 0.15)"
    verdict_border = "#10B981" if passed else "#ED1C24"
    
    # Encode images if provided
    original_img_html = ""
    if original_image:
        b64 = _encode_image_to_base64(original_image)
        original_img_html = f'<img src="data:image/jpeg;base64,{b64}" alt="Original Image" style="width:100%; border-radius:8px; border: 1px solid #2E3340;">'
    
    annotated_img_html = ""
    if annotated_image:
        b64 = _encode_image_to_base64(annotated_image)
        annotated_img_html = f'<img src="data:image/jpeg;base64,{b64}" alt="Annotated Image" style="width:100%; border-radius:8px; border: 1px solid #2E3340;">'
    
    # Build items table rows
    items_rows = ""
    for item in items:
        status = item.get("status", "present")
        color = _get_status_color(status)
        label = _get_status_label(status)
        name = item.get("id", "unknown").replace("_", " ").title()
        expected = item.get("expected_count", 0)
        detected = item.get("detected_count", 0)
        confidence = item.get("confidence", 0)
        note = item.get("note", "")
        
        items_rows += f"""
        <tr>
            <td style="font-weight:600;">{name}</td>
            <td style="text-align:center;">{expected}</td>
            <td style="text-align:center;">{detected}</td>
            <td style="text-align:center;">
                <span style="color:{color}; font-weight:600;">{label}</span>
            </td>
            <td style="text-align:center;">
                <div style="display:flex; align-items:center; gap:8px; justify-content:center;">
                    <div style="background:#1A1D23; border-radius:4px; width:80px; height:8px; overflow:hidden;">
                        <div style="width:{confidence}%; height:100%; background:{color}; border-radius:4px;"></div>
                    </div>
                    <span style="font-size:0.85rem;">{confidence}%</span>
                </div>
            </td>
            <td style="font-size:0.85rem; color:#8B919A;">{note if note else '—'}</td>
        </tr>
        """
    
    # Build the full HTML report
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AsBuilt Lens — Inspection Report — {timestamp}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #1A1D23;
            color: #FFFFFF;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 2rem 0;
            border-bottom: 2px solid #E8640A;
            margin-bottom: 2rem;
        }}
        .header h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 0.25rem;
        }}
        .header .tagline {{
            color: #8B919A;
            font-size: 0.9rem;
            font-weight: 300;
        }}
        .header .report-type {{
            display: inline-block;
            background: #E8640A;
            color: white;
            padding: 0.3rem 1rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-top: 1rem;
        }}
        
        /* Verdict Banner */
        .verdict {{
            background: {verdict_bg};
            border: 2px solid {verdict_border};
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .verdict h2 {{
            font-size: 2rem;
            font-weight: 800;
            color: {verdict_color};
            letter-spacing: 0.05em;
        }}
        .verdict .stats {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 0.75rem;
            flex-wrap: wrap;
        }}
        .verdict .stat {{
            text-align: center;
        }}
        .verdict .stat .value {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #FFFFFF;
        }}
        .verdict .stat .label {{
            font-size: 0.7rem;
            color: #8B919A;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Sections */
        .section {{
            background: #22262E;
            border: 1px solid #2E3340;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .section h3 {{
            color: #E8640A;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Meta Grid */
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        .meta-item {{
            background: #1A1D23;
            border: 1px solid #2E3340;
            border-radius: 8px;
            padding: 1rem;
        }}
        .meta-item .label {{
            font-size: 0.7rem;
            color: #8B919A;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }}
        .meta-item .value {{
            font-size: 0.95rem;
            font-weight: 600;
            color: #FFFFFF;
        }}
        
        /* Items Table */
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #1A1D23;
            color: #8B919A;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid #2E3340;
        }}
        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #2E3340;
            color: #FFFFFF;
            font-size: 0.9rem;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover {{
            background: rgba(232, 100, 10, 0.05);
        }}
        
        /* Images Grid */
        .images-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }}
        .images-grid .single {{
            grid-column: 1 / -1;
        }}
        .image-label {{
            font-size: 0.75rem;
            color: #8B919A;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}
        
        /* Summary */
        .summary-text {{
            background: #1A1D23;
            border-left: 3px solid #E8640A;
            padding: 1rem 1.25rem;
            border-radius: 0 8px 8px 0;
            color: #FFFFFF;
            font-size: 0.95rem;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem 0 1rem;
            border-top: 1px solid #2E3340;
            margin-top: 2rem;
        }}
        .footer p {{
            color: #5A5F6A;
            font-size: 0.75rem;
        }}
        .footer .brand {{
            color: #E8640A;
            font-weight: 600;
        }}
        
        /* Print styles */
        @media print {{
            body {{ background: white; color: black; }}
            .container {{ max-width: 100%; padding: 1rem; }}
            .section {{ border: 1px solid #ddd; }}
            .verdict {{ border: 2px solid {verdict_border}; }}
            th {{ background: #f5f5f5; color: #333; }}
            td {{ color: #333; }}
            .meta-item {{ background: #f9f9f9; border: 1px solid #ddd; }}
            .summary-text {{ background: #f9f9f9; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔍 AsBuilt Lens</h1>
            <p class="tagline">Describe what should exist. The AI verifies it visually.</p>
            <div class="report-type">Inspection Report</div>
        </div>
        
        <!-- Verdict -->
        <div class="verdict">
            <h2>INSPECTION {verdict_text}</h2>
            <div class="stats">
                <div class="stat">
                    <div class="value">{passed_items}/{total_items}</div>
                    <div class="label">Items Verified</div>
                </div>
                <div class="stat">
                    <div class="value">{avg_confidence:.0f}%</div>
                    <div class="label">Avg Confidence</div>
                </div>
                <div class="stat">
                    <div class="value">{elapsed_str}</div>
                    <div class="label">Analysis Time</div>
                </div>
                <div class="stat">
                    <div class="value">{missing_items}</div>
                    <div class="label">Missing</div>
                </div>
                <div class="stat">
                    <div class="value">{anomaly_items}</div>
                    <div class="label">Anomalies</div>
                </div>
            </div>
        </div>
        
        <!-- Inspection Metadata -->
        <div class="section">
            <h3>📋 Inspection Details</h3>
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="label">Date & Time</div>
                    <div class="value">{date_display}</div>
                </div>
                <div class="meta-item">
                    <div class="label">Model</div>
                    <div class="value">Qwen3-VL-32B</div>
                </div>
                <div class="meta-item">
                    <div class="label">Infrastructure</div>
                    <div class="value">AMD MI300X</div>
                </div>
                <div class="meta-item">
                    <div class="label">Inference Engine</div>
                    <div class="value">vLLM on ROCm</div>
                </div>
            </div>
        </div>
        
        <!-- Specification -->
        <div class="section">
            <h3>📝 Inspection Specification</h3>
            <div class="summary-text">
                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">{specification}</pre>
            </div>
        </div>
        
        <!-- Images -->
        <div class="section">
            <h3>🖼️ Inspection Images</h3>
            <div class="images-grid{' single' if not (original_img_html and annotated_img_html) else ''}">
                {"<div>" + "<p class='image-label'>Original</p>" + original_img_html + "</div>" if original_img_html else ""}
                {"<div>" + "<p class='image-label'>Annotated Result</p>" + annotated_img_html + "</div>" if annotated_img_html else ""}
            </div>
        </div>
        
        <!-- Item Details -->
        <div class="section">
            <h3>📊 Item-by-Item Results</h3>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th style="text-align:center;">Expected</th>
                            <th style="text-align:center;">Detected</th>
                            <th style="text-align:center;">Status</th>
                            <th style="text-align:center;">Confidence</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Summary -->
        <div class="section">
            <h3>📝 Summary</h3>
            <div class="summary-text">{summary}</div>
            {"<div class='summary-text' style='margin-top:0.75rem; border-left-color:#F59E0B;'><strong>Notes:</strong> " + notes + "</div>" if notes else ""}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Generated by <span class="brand">AsBuilt Lens</span> — Zero-Shot Visual Inspection</p>
            <p>AMD Developer Hackathon 2026 · Track 3: Vision & Multimodal AI</p>
            <p>Report generated: {timestamp}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def get_report_filename() -> str:
    """Generate a timestamped filename for the report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"AsBuilt_Lens_Report_{timestamp}.html"
