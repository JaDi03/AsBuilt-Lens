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
        "present": "[PASS] PRESENT",
        "missing": "[FAIL] MISSING",
        "anomaly": "[WARN] ANOMALY",
        "unexpected": "[UNEX] UNEXPECTED",
    }
    return labels.get(status, "❓ UNKNOWN")


def get_logo_html() -> str:
    """Read local logo and convert to base64 for embedding."""
    try:
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo1.PNG")
        if os.path.exists(logo_path):
            from PIL import Image
            img = Image.open(logo_path)
            b64 = _encode_image_to_base64(img, max_width=300)
            return f'<img src="data:image/png;base64,{b64}" alt="AsBuilt Lens" style="height: 38px; margin-bottom: 0.5rem;">'
    except Exception as e:
        print(f"Error loading logo: {e}")
    return '<div style="font-weight: 800; font-size: 1.2rem; color: #E8640A; letter-spacing: 0.05em; margin-bottom: 0.5rem;">AsBuilt Lens</div>'


def generate_inspection_report(
    result: Dict,
    specification: str,
    elapsed: float,
    original_image: Optional[Image.Image] = None,
    annotated_image: Optional[Image.Image] = None,
    inspector_name: str = "Automated System",
    job_id: str = "N/A",
) -> str:
    """
    Generate a self-contained HTML inspection report.
    
    Args:
        result: Parsed inspection result dict with items, summary, etc.
        specification: The original inspection specification text.
        elapsed: Elapsed time in seconds.
        original_image: The original captured/uploaded image.
        annotated_image: The annotated image with bounding boxes and badge.
        inspector_name: Name of the operator.
        job_id: Lot or Job identifier.
    
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
    
    # Verdict styling & Disposition
    verdict_color = "#10B981" if passed else "#ED1C24"
    verdict_text = "PASSED" if passed else "FAILED"
    verdict_bg = "rgba(16, 185, 129, 0.15)" if passed else "rgba(237, 28, 36, 0.15)"
    verdict_border = "#10B981" if passed else "#ED1C24"
    
    disposition_text = "APPROVED FOR NEXT STAGE" if passed else "QUARANTINED / ROUTED TO REWORK"
    disposition_color = "#10B981" if passed else "#ED1C24"
    
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
                <span style="color:{color}; font-weight:700;">{label}</span>
            </td>
            <td style="text-align:center;">
                <div style="display:flex; align-items:center; gap:8px; justify-content:center;">
                    <div style="background:#E5E7EB; border-radius:4px; width:60px; height:6px; overflow:hidden;">
                        <div style="width:{confidence}%; height:100%; background:{color}; border-radius:4px;"></div>
                    </div>
                    <span style="font-size:0.85rem; color:#4B5563; font-weight:600;">{confidence}%</span>
                </div>
            </td>
            <td style="font-size:0.85rem; color:#6B7280;">{note if note else '—'}</td>
        </tr>
        """
        
    # Build CAR (Corrective Action Request) section
    car_html = ""
    car_plan = result.get("corrective_action_plan", {})
    if car_plan.get("status") == "REQUIRED":
        car_rows = ""
        for action in car_plan.get("actions", []):
            issue = action.get("issue", "").upper()
            part = action.get("part_number", "N/A")
            sop = action.get("repair_sop", "N/A")
            car_rows += f"""
            <div style="background: #FEF2F2; border-left: 4px solid #EF4444; padding: 1rem; margin-bottom: 0.75rem; border-radius: 0 4px 4px 0; border: 1px solid #FEE2E2; border-left-width: 4px;">
                <div style="display:flex; justify-content:space-between; margin-bottom: 0.25rem;">
                    <strong style="color: #111827;">Part: {part}</strong>
                    <span style="color:#EF4444; font-size:0.8rem; font-weight:bold;">{issue}</span>
                </div>
                <div style="font-size:0.85rem; color:#4B5563;"><strong>Repair SOP:</strong> {sop}</div>
            </div>
            """
            
        car_html = f"""
        <div class="section">
            <h3 style="color: #EF4444; border-bottom-color: #FEE2E2;">Corrective Action Request (CAR)</h3>
            <p style="font-size: 0.85rem; color: #4B5563; margin-bottom: 1rem;">
                The autonomous agent has identified the following required actions based on the MES database:
            </p>
            {car_rows}
        </div>
        """
    
    # Build the full HTML report
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AsBuilt Lens — Inspection Report — {{timestamp}}</title>
    <!-- Include html2pdf.js for client-side PDF generation -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #E5E7EB;
            color: #111827;
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        
        .floating-btn {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: #E8640A;
            color: white;
            border: none;
            padding: 1rem 1.5rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(232, 100, 10, 0.4);
            z-index: 1000;
            transition: all 0.2s;
        }}
        .floating-btn:hover {{ background: #cc5809; transform: translateY(-2px); }}
        
        .document {{
            max-width: 850px;
            margin: 0 auto;
            background: #FFFFFF;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-top: 8px solid #E8640A;
        }}
        
        .container {{ padding: 3rem 4rem; }}
        
        /* Header */
        .header {{ border-bottom: 2px solid #F3F4F6; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        .header h1 {{ font-size: 1.8rem; font-weight: 800; color: #111827; }}
        .header .tagline {{ color: #6B7280; font-size: 0.9rem; margin-top: 0.25rem; }}
        .report-type {{ display: inline-block; background: #111827; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
        
        /* Verdict Banner */
        .verdict {{ background: {verdict_bg}; border: 1px solid {verdict_border}; border-radius: 8px; padding: 1.5rem; text-align: center; margin-bottom: 2rem; }}
        .verdict h2 {{ font-size: 1.8rem; font-weight: 800; color: {verdict_color}; letter-spacing: 0.05em; margin-bottom: 1rem; }}
        .verdict .stats {{ display: flex; justify-content: center; gap: 2.5rem; flex-wrap: wrap; }}
        .verdict .stat {{ text-align: center; }}
        .verdict .stat .value {{ font-size: 1.2rem; font-weight: 700; color: #111827; }}
        .verdict .stat .label {{ font-size: 0.7rem; color: #6B7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }}
        
        /* Sections */
        .section {{ margin-bottom: 2rem; page-break-inside: avoid; }}
        .section h3 {{ color: #374151; font-size: 1rem; font-weight: 700; border-bottom: 1px solid #E5E7EB; padding-bottom: 0.5rem; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        
        /* Meta Grid */
        .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; background: #F9FAFB; padding: 1.5rem; border-radius: 8px; border: 1px solid #E5E7EB; }}
        .meta-item .label {{ font-size: 0.7rem; color: #6B7280; text-transform: uppercase; font-weight: 600; }}
        .meta-item .value {{ font-size: 0.95rem; font-weight: 600; color: #111827; }}
        
        /* Items Table */
        table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
        th {{ background: #F9FAFB; color: #4B5563; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; padding: 0.75rem 1rem; text-align: left; border-bottom: 2px solid #E5E7EB; }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #E5E7EB; color: #111827; font-size: 0.9rem; }}
        tr:nth-child(even) {{ background: #F9FAFB; }}
        tr {{ page-break-inside: avoid; page-break-after: auto; }}
        
        /* Images Grid */
        .images-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
        .images-grid .single {{ grid-column: 1 / -1; }}
        .image-label {{ font-size: 0.8rem; font-weight: 600; color: #4B5563; text-transform: uppercase; margin-bottom: 0.5rem; }}
        
        /* Summary */
        .summary-text {{ background: #F9FAFB; border-left: 4px solid #E8640A; padding: 1rem 1.5rem; color: #374151; font-size: 0.95rem; line-height: 1.6; border-radius: 0 4px 4px 0; }}
        
        /* Footer */
        .footer {{ text-align: center; padding-top: 2rem; border-top: 1px solid #E5E7EB; margin-top: 3rem; }}
        .footer p {{ color: #6B7280; font-size: 0.75rem; margin-bottom: 0.25rem; }}
        .footer .brand {{ color: #E8640A; font-weight: 700; }}
        
        /* Print/PDF Mode hiding */
        @media print {{
            body {{ background: white; padding: 0; }}
            .document {{ box-shadow: none; max-width: 100%; border-top: none; }}
            .container {{ padding: 0; }}
            .floating-btn {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <button class="floating-btn no-print" onclick="generatePDF()" id="downloadBtn">📥 Download PDF</button>

    <div class="document" id="report-content">
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h1>AsBuilt Lens</h1>
                        <p class="tagline">Formal Inspection Certificate</p>
                    </div>
                    <div style="text-align: right;">
                        {get_logo_html()}
                    </div>
                </div>
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
                <h3>Inspection Metadata</h3>
                <div class="meta-grid">
                    <div class="meta-item">
                        <div class="label">Job / Lot Number</div>
                        <div class="value">{job_id}</div>
                    </div>
                    <div class="meta-item">
                        <div class="label">Inspector Name</div>
                        <div class="value">{inspector_name}</div>
                    </div>
                    <div class="meta-item">
                        <div class="label">Date & Time</div>
                        <div class="value">{date_display}</div>
                    </div>
                    <div class="meta-item">
                        <div class="label">Disposition Status</div>
                        <div class="value" style="color: {disposition_color};">{disposition_text}</div>
                    </div>
                    <div class="meta-item">
                        <div class="label">Inference Engine</div>
                        <div class="value">vLLM on ROCm (AMD MI300X)</div>
                    </div>
                    <div class="meta-item">
                        <div class="label">Vision Model</div>
                        <div class="value">Qwen3-VL-32B</div>
                    </div>
                </div>
            </div>
            
            <!-- Images -->
            <div class="section">
                <h3>Visual Evidence</h3>
                <div class="images-grid{' single' if not (original_img_html and annotated_img_html) else ''}">
                    {"<div>" + "<div class='image-label'>Original Capture</div>" + original_img_html + "</div>" if original_img_html else ""}
                    {"<div>" + "<div class='image-label'>AI Annotation Analysis</div>" + annotated_img_html + "</div>" if annotated_img_html else ""}
                </div>
            </div>
            
            <!-- Item Details -->
            <div class="section">
                <h3>Itemized Verification Log</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Component</th>
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
            
            <!-- Summary -->
            <div class="section">
                <h3>Executive Summary</h3>
                <div class="summary-text">{summary}</div>
                {"<div class='summary-text' style='margin-top:0.75rem; border-left-color:#F59E0B;'><strong>Notes:</strong> " + notes + "</div>" if notes else ""}
            </div>
            
            <!-- Specification -->
            <div class="section">
                <h3>Applied Specification</h3>
                <div style="background: #F9FAFB; padding: 1rem; border: 1px solid #E5E7EB; border-radius: 4px; font-family: monospace; font-size: 0.85rem; color: #4B5563; white-space: pre-wrap;">{specification}</div>
            </div>
            
            <!-- Corrective Action Request (Dynamic) -->
            {car_html}
            
            <!-- Footer -->
            <div class="footer">
                <p>Generated by <span class="brand">AsBuilt Lens</span> — Autonomous Quality Assurance</p>
                <p>Report Document ID: {timestamp.replace(' ', '_').replace(':', '')}</p>
            </div>
        </div>
    </div>

    <script>
        function generatePDF() {{
            const btn = document.getElementById('downloadBtn');
            btn.innerHTML = "⏳ Generating...";
            btn.style.opacity = "0.7";
            
            const element = document.getElementById('report-content');
            
            const opt = {{
                margin:       [0.5, 0, 0.5, 0],
                filename:     'AsBuilt_Report_{timestamp.replace(' ', '_').replace(':', '')}.pdf',
                image:        {{ type: 'jpeg', quality: 0.98 }},
                html2canvas:  {{ scale: 2, useCORS: true, scrollY: 0 }},
                jsPDF:        {{ unit: 'in', format: 'letter', orientation: 'portrait' }}
            }};
            
            // Promise-based generation
            html2pdf().set(opt).from(element).save().then(() => {{
                btn.innerHTML = "✅ Downloaded";
                setTimeout(() => {{
                    btn.innerHTML = "📥 Download PDF";
                    btn.style.opacity = "1";
                }}, 3000);
            }});
        }}
    </script>
</body>
</html>"""
    
    return html


def get_report_filename() -> str:
    """Generate a timestamped filename for the report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"AsBuilt_Lens_Report_{timestamp}.html"


def generate_batch_report(batch_data: Dict) -> str:
    """
    Generate a self-contained HTML consolidated batch inspection report.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    total_imgs = batch_data["images_count"]
    total_elapsed = batch_data["total_elapsed"]
    img_per_min = (total_imgs / total_elapsed) * 60 if total_elapsed > 0 else 0
    
    results = batch_data["results"]
    
    passed_count = sum(1 for r in results if not r.get("error") and r.get("result") and r["result"].get("inspection_passed"))
    
    verdict_color = "#10B981" if passed_count == total_imgs else "#F59E0B"
    verdict_text = "ALL PASSED" if passed_count == total_imgs else "PARTIAL PASS"
    if passed_count == 0:
        verdict_color = "#ED1C24"
        verdict_text = "ALL FAILED"
        
    verdict_border = verdict_color
    verdict_bg = "rgba(16, 185, 129, 0.15)" if passed_count == total_imgs else "rgba(245, 158, 11, 0.15)"
    
    # Generate rows for each image
    images_rows = ""
    for i, r in enumerate(results):
        if r.get("error"):
            status_html = '<span style="color:#ED1C24; font-weight:bold;">[ERROR]</span>'
            img_html = ""
            details = r["error"]
        else:
            res_data = r["result"]
            passed = res_data.get("inspection_passed", False)
            status_color = "#10B981" if passed else "#ED1C24"
            status_text = "[PASS]" if passed else "[FAIL]"
            status_html = f'<span style="color:{status_color}; font-weight:bold;">{status_text}</span>'
            
            b64 = _encode_image_to_base64(r["annotated_image"], max_width=400)
            img_html = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%; max-width:300px; border-radius:4px;">'
            
            # Simple details
            items = res_data.get("items", [])
            details = "<ul style='margin-left: 20px; font-size: 0.85rem;'>"
            for item in items:
                st_name = item.get("id", "unknown").replace("_", " ").title()
                st_stat = item.get("status", "present").upper()
                c_color = _get_status_color(item.get("status", "present"))
                details += f"<li>{st_name}: <span style='color:{c_color}'>[{st_stat}]</span></li>"
            details += "</ul>"
        
        images_rows += f"""
        <tr>
            <td style="text-align:center; font-weight:bold;">#{i+1}</td>
            <td style="text-align:center;">{status_html}</td>
            <td style="text-align:center;">{img_html}</td>
            <td>{details}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AsBuilt Lens — Batch Inspection Report — {{timestamp}}</title>
    <!-- Include html2pdf.js for client-side PDF generation -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #E5E7EB; color: #111827; line-height: 1.6; padding: 2rem 1rem; }}
        
        .floating-btn {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: #E8640A;
            color: white;
            border: none;
            padding: 1rem 1.5rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(232, 100, 10, 0.4);
            z-index: 1000;
            transition: all 0.2s;
        }}
        .floating-btn:hover {{ background: #cc5809; transform: translateY(-2px); }}
        
        .document {{ max-width: 900px; margin: 0 auto; background: #FFFFFF; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-top: 8px solid #E8640A; }}
        .container {{ padding: 3rem 4rem; }}
        
        .header {{ border-bottom: 2px solid #F3F4F6; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        .header h1 {{ font-size: 1.8rem; font-weight: 800; color: #111827; margin-bottom: 0.25rem; }}
        .header .tagline {{ color: #6B7280; font-size: 0.9rem; }}
        .report-type {{ display: inline-block; background: #111827; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-top: 1rem; }}
        
        .verdict {{ background: {verdict_bg}; border: 1px solid {verdict_border}; border-radius: 8px; padding: 1.5rem; text-align: center; margin-bottom: 2rem; }}
        .verdict h2 {{ font-size: 1.8rem; font-weight: 800; color: {verdict_color}; letter-spacing: 0.05em; margin-bottom: 1rem; }}
        .verdict .stats {{ display: flex; justify-content: center; gap: 2.5rem; flex-wrap: wrap; }}
        .verdict .stat {{ text-align: center; }}
        .verdict .stat .value {{ font-size: 1.2rem; font-weight: 700; color: #111827; }}
        .verdict .stat .label {{ font-size: 0.7rem; color: #6B7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }}
        
        .section {{ margin-bottom: 2rem; }}
        .section h3 {{ color: #374151; font-size: 1rem; font-weight: 700; border-bottom: 1px solid #E5E7EB; padding-bottom: 0.5rem; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #F9FAFB; color: #4B5563; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; padding: 0.75rem 1rem; text-align: left; border-bottom: 2px solid #E5E7EB; }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #E5E7EB; color: #111827; font-size: 0.9rem; vertical-align: middle; }}
        tr:nth-child(even) {{ background: #F9FAFB; }}
        tr {{ page-break-inside: avoid; page-break-after: auto; }}
        
        .footer {{ text-align: center; padding-top: 2rem; border-top: 1px solid #E5E7EB; margin-top: 3rem; }}
        .footer p {{ color: #6B7280; font-size: 0.75rem; margin-bottom: 0.25rem; }}
        .footer .brand {{ color: #E8640A; font-weight: 700; }}
        
        @media print {{
            body {{ background: white; padding: 0; }}
            .document {{ box-shadow: none; max-width: 100%; border-top: none; }}
            .container {{ padding: 0; }}
            .floating-btn {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <button class="floating-btn no-print" onclick="generatePDF()" id="downloadBtn">📥 Download PDF</button>

    <div class="document" id="report-content">
        <div class="container">
            <div class="header">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h1>AsBuilt Lens</h1>
                        <p class="tagline">Consolidated Batch Inspection</p>
                    </div>
                    <div style="text-align: right;">
                        {get_logo_html()}
                    </div>
                </div>
            </div>
            
            <div class="verdict">
                <h2>BATCH RESULT: {verdict_text}</h2>
                <div class="stats">
                    <div class="stat">
                        <div class="value">{passed_count}/{total_imgs}</div>
                        <div class="label">Images Passed</div>
                    </div>
                    <div class="stat">
                        <div class="value">{total_elapsed:.1f}s</div>
                        <div class="label">Total Time</div>
                    </div>
                    <div class="stat">
                        <div class="value">{img_per_min:.1f}</div>
                        <div class="label">Img / Min Throughput</div>
                    </div>
                    <div class="stat">
                        <div class="value">Parallel</div>
                        <div class="label">Execution Mode</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>Applied Specification</h3>
                <div style="background: #F9FAFB; padding: 1rem; border: 1px solid #E5E7EB; border-radius: 4px; font-family: monospace; font-size: 0.85rem; color: #4B5563; white-space: pre-wrap;">{batch_data["specification"]}</div>
            </div>
            
            <div class="section">
                <h3>Batch Results Log</h3>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th style="text-align:center; width: 60px;">ID</th>
                                <th style="text-align:center; width: 100px;">Status</th>
                                <th style="text-align:center; width: 320px;">Image</th>
                                <th>Item Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {images_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="footer">
                <p>Generated by <span class="brand">AsBuilt Lens</span> — Autonomous Quality Assurance</p>
                <p>Report Document ID: BATCH_{timestamp.replace(' ', '_').replace(':', '')}</p>
            </div>
        </div>
    </div>

    <script>
        function generatePDF() {{
            const btn = document.getElementById('downloadBtn');
            btn.innerHTML = "⏳ Generating...";
            btn.style.opacity = "0.7";
            
            const element = document.getElementById('report-content');
            
            const opt = {{
                margin:       [0.5, 0, 0.5, 0],
                filename:     'AsBuilt_Batch_Report_{timestamp.replace(' ', '_').replace(':', '')}.pdf',
                image:        {{ type: 'jpeg', quality: 0.98 }},
                html2canvas:  {{ scale: 2, useCORS: true, scrollY: 0 }},
                jsPDF:        {{ unit: 'in', format: 'letter', orientation: 'portrait' }}
            }};
            
            html2pdf().set(opt).from(element).save().then(() => {{
                btn.innerHTML = "✅ Downloaded";
                setTimeout(() => {{
                    btn.innerHTML = "📥 Download PDF";
                    btn.style.opacity = "1";
                }}, 3000);
            }});
        }}
    </script>
</body>
</html>"""
    return html

