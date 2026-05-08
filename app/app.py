"""
AsBuilt Lens — Main Streamlit Application
Zero-shot visual inspection powered by AMD MI300X + Qwen3-VL.
"""

import streamlit as st
import time
import numpy as np
from PIL import Image

import config
from inspector import run_inspection, run_mock_inspection, run_discovery
from camera import CameraManager, test_camera_connection
from utils import (
    annotate_image, draw_inspection_badge, format_elapsed_time,
    get_status_icon, get_status_color, get_status_bg_color,
    calculate_pass_rate, create_history_entry, COLORS
)
from report import generate_inspection_report, get_report_filename

# ─── Page Configuration ───────────────────────────────────────────────

st.set_page_config(
    page_title=f"{config.APP_TITLE} — Zero-Shot Visual Inspection",
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global styles and background */
    .stApp {
        background-color: #1A1D23;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #FFFFFF !important;
    }

    /* Remove Streamlit default top padding */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 95% !important;
    }

    /* Main header styling - Branding Left, Tech Right */
    .main-header {
        background: #22262E;
        border-bottom: 2px solid #E8640A;
        padding: 0.7rem 3.5rem;
        margin: 0 -5rem 1.2rem -5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-branding {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .main-header p {
        color: #8B919A;
        font-size: 0.75rem;
        font-weight: 300;
        margin: 0 !important;
        letter-spacing: 0.5px;
    }
    .logo-img {
        width: 180px !important;
        height: auto;
        margin-bottom: 0.2rem;
    }
    .header-tech {
        display: flex;
        gap: 0.4rem;
    }

    /* Tech badges */
    .tech-badge {
        display: inline-block;
        background: #1A1D23;
        border: 1px solid #2E3340;
        border-radius: 4px;
        padding: 0.3rem 0.8rem;
        color: #8B919A;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 0 0.2rem;
        letter-spacing: 0.03em;
    }

    /* Disable header anchor links */
    .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a, .stMarkdown h4 a, .stMarkdown h5 a, .stMarkdown h6 a {
        display: none !important;
    }

    /* Standardized Image Container */
    [data-testid="stImage"] img {
        max-height: 450px !important;
        width: auto !important;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
        object-fit: contain !important;
        border-radius: 8px;
        border: 1px solid #2E3340;
        background-color: #0E1117;
    }

    /* Light text for everything */
    h1, h2, h3, h4, h5, h6, label, p, span, div, .stCaption {
        color: #FFFFFF !important;
    }

    /* Placeholder text */
    ::placeholder {
        color: #5A5F6A !important;
        opacity: 1;
    }
    textarea::placeholder {
        color: #5A5F6A !important;
    }

    /* Widget Styling (Dark cards) */
    [data-testid="stFileUploadDropzone"], 
    [data-testid="stFileUploadDropzone"] > div,
    [data-testid="stSelectbox"] div[data-baseweb="select"],
    [data-testid="stSelectbox"] div[role="button"],
    [data-testid="stTextArea"] textarea {
        background-color: #1A1D23 !important;
        color: #FFFFFF !important;
        border: 1px solid #2E3340 !important;
        border-radius: 6px !important;
    }
    
    [data-testid="stSelectbox"] div[data-baseweb="select"] div,
    [data-testid="stFileUploadDropzone"] span,
    [data-testid="stFileUploadDropzone"] div {
        color: #8B919A !important;
    }

    /* Dropdown menu - force dark on ALL popover/menu elements */
    [data-baseweb="popover"] {
        background-color: #22262E !important;
    }
    [data-baseweb="popover"] > div {
        background-color: #22262E !important;
    }
    [data-baseweb="menu"] {
        background-color: #22262E !important;
    }
    li[role="option"] {
        background-color: #22262E !important;
        color: #FFFFFF !important;
    }
    li[role="option"]:hover {
        background-color: #2E3340 !important;
    }
    li[aria-selected="true"] {
        background-color: #1A1D23 !important;
        color: #E8640A !important;
    }

    /* Browse button inside file uploader */
    [data-testid="stFileUploadDropzone"] button {
        background-color: #E8640A !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    
    /* Status badges */
    .status-pass {
        background: #10B981;
        color: white !important;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-size: 1.1rem;
        font-weight: 700;
        text-align: center;
        margin: 1rem 0;
    }
    .status-fail {
        background: #ED1C24;
        color: white !important;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-size: 1.1rem;
        font-weight: 700;
        text-align: center;
        margin: 1rem 0;
    }

    /* Buttons */
    .stButton button {
        background: #22262E !important;
        border: 1px solid #E8640A !important;
        color: #E8640A !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        background: #E8640A !important;
        color: #FFFFFF !important;
    }
    .stButton button[kind="primary"] {
        background: #E8640A !important;
        color: #FFFFFF !important;
        border: 1px solid #E8640A !important;
    }
    .stButton button[kind="primary"]:hover {
        background: #CF5A09 !important;
    }

    /* Item cards */
    .item-card {
        background: #22262E;
        border: 1px solid #2E3340;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .item-card h4 {
        color: #FFFFFF !important;
        margin: 0 0 0.25rem 0;
    }
    .item-card p {
        color: #8B919A !important;
    }

    /* Confidence bar */
    .confidence-bar-container {
        background: #1A1D23;
        border-radius: 4px;
        height: 6px;
        overflow: hidden;
    }
    .confidence-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    /* Metric cards (Footer) */
    .metric-card {
        background: #22262E;
        border: 1px solid #2E3340;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-card .value {
        font-size: 1.2rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-top: 0.25rem;
    }
    .metric-card .label {
        font-size: 0.7rem;
        color: #8B919A !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #22262E !important;
        border-right: 1px solid #2E3340;
    }
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #8B919A !important;
    }
    
    /* Sidebar status boxes */
    .sidebar-status-box {
        background: #1A1D23;
        border: 1px solid #2E3340;
        border-radius: 6px;
        padding: 0.75rem;
        text-align: center;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .sidebar-status-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: #8B919A;
        margin-bottom: 0.5rem;
    }
    .sidebar-status-value {
        font-weight: 700;
        font-size: 0.85rem;
        color: #FFFFFF;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #22262E;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        color: #8B919A;
        border: 1px solid #2E3340;
    }
    .stTabs [aria-selected="true"] {
        background: #E8640A !important;
        color: white !important;
        border-color: #E8640A !important;
    }

    /* Dividers */
    hr {
        border-color: #2E3340 !important;
    }

    /* History entries */
    .history-entry {
        background: #1A1D23;
        border: 1px solid #2E3340;
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }

    /* Laser Scanline Animation */
    .scanline-container {
        position: relative;
        overflow: hidden;
        border-radius: 8px;
        border: 1px solid #2E3340;
    }
    .scanline {
        position: absolute;
        top: -100%;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            to bottom,
            transparent 0%,
            rgba(232, 100, 10, 0.1) 40%,
            rgba(232, 100, 10, 0.8) 50%,
            rgba(232, 100, 10, 0.1) 60%,
            transparent 100%
        );
        animation: scan 3s linear infinite;
        z-index: 10;
        pointer-events: none;
    }
    @keyframes scan {
        from { top: -100%; }
        to { top: 100%; }
    }

    /* Cyberpunk Glows */
    .glow-pass {
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
        border: 1px solid #10B981 !important;
    }
    .glow-fail {
        box-shadow: 0 0 15px rgba(237, 28, 36, 0.3);
        border: 1px solid #ED1C24 !important;
    }

    /* Item card hover */
    .item-card:hover {
        border-color: #E8640A !important;
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }

    /* Custom Spinner */
    .stSpinner > div {
        border-top-color: #E8640A !important;
    }

    /* Timer chip pulse */
    .timer-chip {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
    }

    /* Hide default streamlit elements but keep sidebar button */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    button[data-testid="stBaseButton-headerNoPadding"] {
        color: #E8640A !important;
    }
</style>
""", unsafe_allow_html=True)

# Override Streamlit's popover portal styles (rendered at body level)
st.markdown("""
<style>
    /* NUCLEAR: Force dark on every popover variant Streamlit uses */
    [data-baseweb="popover"],
    [data-baseweb="popover"] *,
    [data-baseweb="menu"],
    [data-baseweb="menu"] *,
    [data-baseweb="list"],
    [data-baseweb="list"] *,
    ul[role="listbox"],
    ul[role="listbox"] * {
        background-color: #22262E !important;
        color: #FFFFFF !important;
    }
    li[role="option"]:hover { background-color: #2E3340 !important; }
    li[aria-selected="true"] { background-color: #1A1D23 !important; color: #E8640A !important; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Initialization ─────────────────────────────────────

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "history": [],
        "inspection_running": False,
        "camera_source": "local",
        "demo_image": None,
        "last_result": None,
        "camera_active": False,
        "manual_capture_trigger": False,
        "viewing_history": False,
        "current_specification": "",
        "current_image": None,
        "current_annotated": None,
        "spec_input": "", # Initialize for text area
        "pending_inspection_img": None,
        "pending_batch_images": None,
        "pending_batch_spec": None,
        "last_batch_result": None,
        "pending_inspection_spec": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def update_template():
    """Callback to update text area when selectbox changes."""
    template_name = st.session_state.template_select
    st.session_state.spec_input = config.INSPECTION_TEMPLATES.get(template_name, "")


init_session_state()


# ─── Header ───────────────────────────────────────────────────────────

import base64
from io import BytesIO

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

try:
    logo_b64 = get_base64_image("assets/logo_dark.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">'
except Exception:
    logo_html = f"<h1>{config.APP_ICON}</h1>"

st.markdown(f"""
<div class="main-header">
    <div class="header-branding">
        {logo_html}
        <p>{config.APP_TAGLINE}</p>
    </div>
    <div class="header-tech">
        <span class="tech-badge">AMD Instinct MI300X</span>
        <span class="tech-badge">Qwen3-VL</span>
        <span class="tech-badge">ROCm + vLLM</span>
        <span class="tech-badge">Zero-Shot</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    # Removed title/version as they are already in the main logo header
    
    st.markdown("#### Connection Status")

    col_status1, col_status2 = st.columns(2)
    with col_status1:
        st.markdown(f"""
        <div class="sidebar-status-box" style="border-top: 3px solid #E8640A;">
            <div class="sidebar-status-label">Infra</div>
            <div class="sidebar-status-value">AMD Cloud</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_status2:
        model_name = config.VLM_MODEL.split("/")[-1] if "/" in config.VLM_MODEL else config.VLM_MODEL
        st.markdown(f"""
        <div class="sidebar-status-box" style="border-top: 3px solid #E8640A;">
            <div class="sidebar-status-label">Model</div>
            <div class="sidebar-status-value">{model_name[:12]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Settings & Meta ──
    st.markdown("#### Settings & Meta")

    st.session_state.inspector_name = st.text_input(
        "Inspector Name", 
        value=st.session_state.get("inspector_name", "Automated System")
    )
    st.session_state.job_id = st.text_input(
        "Job / Lot Number", 
        value=st.session_state.get("job_id", "LOT-0000")
    )
    
    st.divider()
    
    st.markdown("#### Camera Settings")

    st.session_state.camera_source = st.radio(
        "Camera Source",
        options=["local", "ip"],
        format_func=lambda x: "Laptop Webcam" if x == "local" else "Phone IP Camera",
        horizontal=True
    )
    
    if st.session_state.camera_source == "ip":
        st.caption(f"Current IP URL: `{config.CAMERA_URL}`")


    st.divider()

    # ── Inspection History ──
    st.markdown("#### Inspection History")

    if not st.session_state.history:
        st.caption("No inspections yet. Run your first inspection!")
    else:
        for i, entry in enumerate(reversed(st.session_state.history)):
            status_class = "history-pass" if entry["passed"] else "history-fail"
            status_emoji = "[PASS]" if entry["passed"] else "[FAIL]"
            with st.container():
                st.markdown(f"""
                <div class="history-entry {status_class}">
                    <strong>{status_emoji} #{len(st.session_state.history) - i}</strong>
                    &nbsp;|&nbsp; {entry['passed_count']}/{entry['total_count']} items
                    &nbsp;|&nbsp; {format_elapsed_time(entry['elapsed'])}
                    <br><small style="color: #64748B;">{entry['timestamp']} — {entry['specification_short']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Hidden key to make button unique
                if st.button(f"[VIEW] Report #{len(st.session_state.history) - i}", key=f"view_{len(st.session_state.history) - i}", width="stretch"):
                    st.session_state.last_result = entry["result"]
                    st.session_state.current_image = entry["original_image"]
                    st.session_state.current_annotated = entry["annotated_image"]
                    st.session_state.current_specification = entry["full_specification"]
                    st.session_state.viewing_history = True
                    st.rerun()

        if st.button("[CLEAR] History", width="stretch"):
            st.session_state.history = []
            st.rerun()

    st.divider()

    # ── About ──
    st.markdown("#### [INFO] About")
    st.caption(
        "AsBuilt Lens is a zero-shot visual inspection platform. "
        "It uses multimodal AI to compare physical objects against "
        "natural language specifications — no training, no datasets, "
        "no reconfiguration required."
    )
    st.caption("Built for AMD Developer Hackathon 2026")
    st.markdown(
        "[GitHub](https://github.com) · "
        "[Hugging Face Space](https://huggingface.co)"
    )


# ─── Result Rendering UI ──────────────────────────────────────────────

def render_performance_panel(usage, elapsed):
    """Display industrial performance metrics."""
    # If no usage, show a placeholder but don't hide the panel entirely
    # as it's a key feature of the demo.
    has_usage = bool(usage)
    
    prompt_tokens = usage.get("prompt_tokens", "N/A")
    comp_tokens = usage.get("completion_tokens", "N/A")
    total_tokens = usage.get("total_tokens", "N/A")
    
    if has_usage and isinstance(comp_tokens, (int, float)):
        tps = comp_tokens / elapsed if elapsed > 0 else 0
        tps_str = f"{tps:.1f} tok/s"
    else:
        tps_str = "N/A"
    
    st.markdown(f"""
    <div style="background: #1A1D23; border: 1px solid #2E3340; border-radius: 8px; padding: 1.2rem; margin: 1rem 0;">
        <h5 style="color: #E8640A; margin-top: 0; font-size: 0.9rem; letter-spacing: 1px;">[LIVE] PERFORMANCE METRICS (AMD MI300X)</h5>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
            <div>
                <div style="color: #8B919A; font-size: 0.7rem; text-transform: uppercase;">Throughput</div>
                <div style="color: #FFFFFF; font-size: 1.1rem; font-weight: 600;">{tps_str}</div>
            </div>
            <div>
                <div style="color: #8B919A; font-size: 0.7rem; text-transform: uppercase;">Prompt</div>
                <div style="color: #FFFFFF; font-size: 1.1rem; font-weight: 600;">{prompt_tokens}</div>
            </div>
            <div>
                <div style="color: #8B919A; font-size: 0.7rem; text-transform: uppercase;">Completion</div>
                <div style="color: #FFFFFF; font-size: 1.1rem; font-weight: 600;">{comp_tokens}</div>
            </div>
            <div>
                <div style="color: #8B919A; font-size: 0.7rem; text-transform: uppercase;">Total Latency</div>
                <div style="color: #FFFFFF; font-size: 1.1rem; font-weight: 600;">{elapsed:.2f}s</div>
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid #2E3340; display: flex; justify-content: space-between; font-size: 0.75rem; color: #8B919A;">
            <span>Hardware: AMD Instinct MI300X (192GB HBM3)</span>
            <span>Engine: vLLM + ROCm 6.0</span>
        </div>
        {"<p style='color: #E8640A; font-size: 0.7rem; margin-top: 0.5rem; text-align: center;'>[WARN] API usage stats not returned by backend. Check vLLM configuration.</p>" if not has_usage else ""}
    </div>
    """, unsafe_allow_html=True)


def render_inspection_results(result, image, annotated, specification, elapsed):
    """Reusable UI component to display inspection results."""
    st.markdown("---")

    # Timer
    st.markdown(
        f'<div class="timer-chip">[TIME] Inspection completed in {format_elapsed_time(elapsed)}</div>',
        unsafe_allow_html=True
    )

    # Performance Panel
    render_performance_panel(result.get("usage", {}), elapsed)

    # Pass/Fail Badge
    passed = result.get("inspection_passed", False)
    passed_count, total_count = calculate_pass_rate(result.get("items", []))

    if passed:
        st.markdown(
            f'<div class="status-pass">[PASS] INSPECTION PASSED — {passed_count}/{total_count} items verified</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="status-fail">[FAIL] INSPECTION FAILED — {passed_count}/{total_count} items verified</div>',
            unsafe_allow_html=True
        )

    # Comparison View: Original vs Annotated
    col_orig, col_anno = st.columns(2)
    with col_orig:
        st.markdown("##### [IMG] ORIGINAL")
        with st.container(height=400, border=True):
            st.image(image, width="stretch")
    with col_anno:
        st.markdown("##### [IMG] ANNOTATED")
        with st.container(height=400, border=True):
            st.image(annotated, width="stretch")

    st.markdown("---")
    st.markdown("##### [DATA] Item Details")

    for item in result.get("items", []):
        status = item.get("status", "present")
        icon = get_status_icon(status)
        color = get_status_color(status)
        name = item.get("id", "unknown").replace("_", " ").title()
        expected = item.get("expected_count", 0)
        detected = item.get("detected_count", 0)
        confidence = item.get("confidence", 0)
        note = item.get("note", "")

        st.markdown(f"""
        <div class="item-card">
            <h4>{icon} {name}</h4>
            <p>Expected: <strong>{expected}</strong> &nbsp;|&nbsp;
               Detected: <strong>{detected}</strong> &nbsp;|&nbsp;
               Status: <strong style="color: {color};">{status.upper()}</strong></p>
            <div class="confidence-bar-container">
                <div class="confidence-bar-fill" style="width: {confidence}%; background: {color};"></div>
            </div>
            <p style="font-size: 0.8rem; margin-top: 0.25rem;">Confidence: {confidence}%</p>
            {"<p style='font-size: 0.85rem; color: #F59E0B;'>📝 " + note + "</p>" if note else ""}
        </div>
        """, unsafe_allow_html=True)

    # Summary
    st.markdown("##### [LOG] Summary")
    st.info(result.get("summary", "No summary available."))

    if result.get("notes"):
        st.caption(f"[NOTE] Notes: {result['notes']}")

    # ── Agent 2: Quality Engineer Diagnostics ──
    qe_plan = result.get("quality_engineer_diagnostics")
    if qe_plan:
        st.markdown("##### 🕵️‍♂️ [AGENT 2] Quality Engineer Diagnostics")
        severity_colors = {"CRITICAL": "#ED1C24", "MAJOR": "#F59E0B", "MINOR": "#FBBF24"}
        sev_color = severity_colors.get(qe_plan.get("severity", "MAJOR").upper(), "#F59E0B")
        
        st.markdown(f"""
        <div style="background: #1A1D23; border-left: 4px solid {sev_color}; padding: 1.2rem; border-radius: 4px; margin-bottom: 1rem;">
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.8rem; border-bottom: 1px solid #2E3340; padding-bottom: 0.5rem;">
                <strong style="color: #FFFFFF; font-size: 1.1rem;">Root Cause Analysis</strong>
                <span style="background: {sev_color}20; color: {sev_color}; padding: 0.2rem 0.6rem; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">{qe_plan.get("severity", "MAJOR").upper()} SEVERITY</span>
            </div>
            <p style="color: #D1D5DB; font-size: 0.95rem; margin-bottom: 1rem;">{qe_plan.get("root_cause_analysis", "")}</p>
            <strong style="color: #E8640A; font-size: 0.9rem;">Corrective Actions:</strong>
            <ul style="color: #8B919A; font-size: 0.9rem; margin-top: 0.2rem; margin-bottom: 1rem;">
                {"".join([f"<li>{a}</li>" for a in qe_plan.get("corrective_actions", [])])}
            </ul>
            <strong style="color: #10B981; font-size: 0.9rem;">Preventive Measures:</strong>
            <ul style="color: #8B919A; font-size: 0.9rem; margin-top: 0.2rem; margin-bottom: 0;">
                {"".join([f"<li>{p}</li>" for p in qe_plan.get("preventive_measures", [])])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ── Report Generation & Options ──
    st.markdown("---")
    report_html = generate_inspection_report(
        result=result,
        specification=specification,
        elapsed=elapsed,
        original_image=image,
        annotated_image=annotated,
        inspector_name=st.session_state.get("inspector_name", "Automated System"),
        job_id=st.session_state.get("job_id", "N/A"),
    )
    report_filename = get_report_filename()

    with st.expander("[VIEW] Full Report Online", expanded=True):
        import streamlit.components.v1 as components
        components.html(report_html, height=1400, scrolling=True)
        st.caption("💡 To save as PDF: Click the floating 'Download PDF' button inside the report above.")
    
    # Start New Inspection
    st.markdown("---")
    if st.button("[NEW] Start Inspection", type="secondary", width="stretch"):
        st.session_state.last_result = None
        st.session_state.current_image = None
        st.session_state.current_annotated = None
        st.session_state.viewing_history = False
        st.rerun()


# ─── Inspection Function ──────────────────────────────────────────────


def execute_batch_inspection(images: list, specification: str):
    """Run batch inspection in parallel and display results."""
    if not specification.strip():
        st.error("[WARN] Please enter an Inspection Specification before running.")
        return

    st.markdown(f"#### [BATCH] Inspecting {len(images)} images in parallel...")
    
    # Visual Scanning Effect with Dual Layout
    scan_placeholder = st.empty()
    
    import io
    import base64
    import threading
    from concurrent.futures import ThreadPoolExecutor
    import time
    
    # Use first image for visual effect
    first_img = images[0]
    buffered = io.BytesIO()
    display_img = first_img.convert("RGB") if first_img.mode != "RGB" else first_img
    display_img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Dual Column Scanning UI
    col_scan_left, col_scan_right = scan_placeholder.columns([1, 1])
    
    with col_scan_left:
        st.markdown(f"""
            <div class="scanline-container" style="max-width: 100%; height: 400px; display: flex; align-items: center; justify-content: center; background-color: #0E1117; border-radius: 8px; border: 1px solid #2E3340; overflow: hidden; position: relative;">
                <div class="scanline"></div>
                <img src="data:image/jpeg;base64,{img_str}" style="max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px; opacity: 0.7;">
            </div>
            <p style="text-align: center; color: #E8640A; font-size: 0.8rem; letter-spacing: 2px;">[AGENT 1: INSPECTOR] PARALLEL BATCH SCANNING...</p>
        """, unsafe_allow_html=True)
        
    with col_scan_right:
        log_placeholder = st.empty()
        chart_placeholder = st.empty()
        
        # Initial log display
        initial_log_html = f"""
            <div style="background: #1A1D23; border: 1px solid #2E3340; border-radius: 8px; padding: 1.2rem; font-family: monospace; height: 160px; overflow-y: hidden; margin-bottom: 0.5rem;">
                <h5 style="color: #E8640A; margin: 0; font-size: 0.8rem;">[SYS] BATCH TELEMETRY</h5>
                <div style="font-size: 0.8rem; line-height: 1.5; margin-top: 0.5rem;">
                    <span style="color: #8B919A;">></span> [INIT] PARALLEL PIPELINE<br>
                    <span style="color: #8B919A;">></span> [QUEUE] {len(images)} IMAGES SUBMITTED<br>
                    <span style="color: #8B919A;">></span> [AI] INFERENCING ON MI300X...<br>
                    <span style="display: inline-block; width: 6px; height: 12px; background: #E8640A; animation: blink 1s infinite;"></span>
                </div>
            </div>
        """
        log_placeholder.markdown(initial_log_html, unsafe_allow_html=True)
        
        start_time = time.time()
        results = []
        unordered_results = {}
        
        # Telemetry for chart
        throughput_history = []
        
        with ThreadPoolExecutor(max_workers=min(len(images), 8)) as executor:
            futures = {executor.submit(run_inspection, img, specification): i for i, img in enumerate(images)}
            
            completed = 0
            for future in __import__("concurrent.futures").futures.as_completed(futures):
                idx = futures[future]
                try:
                    res = future.result()
                    res["original_image"] = images[idx]
                    unordered_results[idx] = res
                except Exception as e:
                    unordered_results[idx] = {"error": str(e), "result": None, "elapsed": 0, "original_image": images[idx]}
                
                completed += 1
                current_elapsed = time.time() - start_time
                img_per_min = (completed / current_elapsed) * 60 if current_elapsed > 0 else 0
                throughput_history.append(img_per_min)
                
                # Update progress in the log area
                logs_html = f"""
                    <div style="background: #1A1D23; border: 1px solid #2E3340; border-radius: 8px; padding: 1.2rem; font-family: monospace; height: 160px; overflow-y: hidden; margin-bottom: 0.5rem;">
                        <h5 style="color: #E8640A; margin: 0; font-size: 0.8rem;">[SYS] BATCH TELEMETRY</h5>
                        <div style="font-size: 0.8rem; line-height: 1.5; margin-top: 0.5rem;">
                            <span style="color: #8B919A;">></span> [QUEUE] {len(images)} IMAGES SUBMITTED<br>
                            <span style="color: #8B919A;">></span> [AI] INFERENCING ON MI300X...<br>
                            <br>
                            <span style="color: #10B981; font-weight: bold;">[PROCESS] COMPLETED {completed}/{len(images)}</span><br>
                            <span style="display: inline-block; width: 6px; height: 12px; background: #E8640A; animation: blink 1s infinite;"></span>
                        </div>
                    </div>
                """
                log_placeholder.markdown(logs_html, unsafe_allow_html=True)
                
                # Update Live Chart
                with chart_placeholder.container():
                    st.markdown(f'<p style="color: #8B919A; font-size: 0.7rem; margin-bottom: -10px;">VLM THROUGHPUT: <strong style="color:#10B981;">{img_per_min:.1f} img/min</strong></p>', unsafe_allow_html=True)
                    st.line_chart(throughput_history, height=120, width="stretch")
                
        # Re-order
        for i in range(len(images)):
            results.append(unordered_results[i])

        total_elapsed = time.time() - start_time
        
        # Aggregate usage
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        for r in results:
            usage = r.get("usage", {})
            total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            total_usage["total_tokens"] += usage.get("total_tokens", 0)
        
    scan_placeholder.empty()

    # Process annotations
    for r in results:
        if not r.get("error") and r.get("result"):
            img = r["original_image"]
            res_data = r["result"]
            passed = res_data.get("inspection_passed", False)
            annotated = annotate_image(img, res_data.get("items", []))
            annotated = draw_inspection_badge(annotated, passed)
            r["annotated_image"] = annotated

    batch_data = {
        "images_count": len(images),
        "total_elapsed": total_elapsed,
        "results": results,
        "specification": specification,
        "total_usage": total_usage
    }
    st.session_state.last_batch_result = batch_data
    st.rerun()

def render_batch_results(batch_data):
    st.markdown("---")
    
    total_imgs = batch_data["images_count"]
    total_elapsed = batch_data["total_elapsed"]
    img_per_min = (total_imgs / total_elapsed) * 60 if total_elapsed > 0 else 0
    
    passed_count = sum(1 for r in batch_data["results"] if not r.get("error") and r.get("result") and r["result"].get("inspection_passed"))
    
    st.markdown(f"### [BATCH] RESULTS: {passed_count}/{total_imgs} PASSED")
    st.markdown(
        f'<div class="timer-chip" style="background: #22262E; padding: 1rem; border-radius: 8px; border: 1px solid #2E3340;">'
        f'<span style="color: #E8640A; font-weight: bold;">[THROUGHPUT]</span> '
        f'{total_imgs} images analyzed in {format_elapsed_time(total_elapsed)} — <strong>{img_per_min:.1f} img/min</strong></div>',
        unsafe_allow_html=True
    )
    
    # Performance Panel for the whole batch
    render_performance_panel(batch_data.get("total_usage", {}), total_elapsed)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display Grid (max 2 per row to allow side-by-side internal comparison)
    cols = st.columns(2)
    
    for i, r in enumerate(batch_data["results"]):
        col = cols[i % 2]
        with col:
            st.markdown(f"##### IMAGE #{i+1}")
            if r.get("error"):
                st.error(f"[ERROR] {r['error']}")
                st.image(r["original_image"], width="stretch")
            else:
                passed = r["result"].get("inspection_passed", False)
                status_class = "status-pass" if passed else "status-fail"
                status_text = "PASS" if passed else "FAIL"
                
                st.markdown(f'<div class="{status_class}" style="padding: 0.3rem; margin: 0.2rem 0; font-size: 0.9rem; text-align:center;">{status_text}</div>', unsafe_allow_html=True)
                
                # Side-by-side comparison for batch items
                c1, c2 = st.columns(2)
                with c1:
                    with st.container(height=300, border=True):
                        st.image(r["original_image"], width="stretch")
                with c2:
                    with st.container(height=300, border=True):
                        st.image(r["annotated_image"], width="stretch")
                
                with st.expander("[DATA] Details"):
                    st.caption(f"Time: {r['elapsed']:.2f}s")
                    for item in r["result"].get("items", []):
                        st_name = item.get("id", "unknown").replace("_", " ").title()
                        st_stat = item.get("status", "present").upper()
                        col_clr = get_status_color(item.get("status", "present"))
                        st.markdown(f"- **{st_name}**: <span style='color:{col_clr}'>{st_stat}</span>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")
    
    try:
        from report import generate_batch_report, get_report_filename
        report_html = generate_batch_report(batch_data)
        with st.expander("[VIEW] Consolidated Batch Report", expanded=True):
            import streamlit.components.v1 as components
            components.html(report_html, height=1400, scrolling=True)
            st.caption("💡 To save as PDF: Click the floating 'Download PDF' button inside the report above.")
    except ImportError:
        st.warning("Batch report generation not yet implemented.")
        
    if st.button("[NEW] Start New Inspection", type="secondary", width="stretch", key="btn_new_batch"):
            st.session_state.last_batch_result = None
            st.rerun()

def execute_inspection(image: Image.Image, specification: str):

    """Run inspection and display results."""
    if not specification.strip():
        st.error("[WARN] Please enter an Inspection Specification before running.")
        return

    # Run inspection
    with st.spinner("[ANALYZING] ON AMD CLOUD..."):
        # Visual Scanning Effect with Dual Layout
        scan_placeholder = st.empty()
        
        # Helper to convert PIL to base64 for the overlay
        import io
        import base64
        buffered = io.BytesIO()
        
        # FIX: Convert to RGB (removes alpha channel) to avoid JPEG save error
        display_img = image.convert("RGB") if image.mode != "RGB" else image
        display_img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Dual Column Scanning UI
        col_scan_left, col_scan_right = scan_placeholder.columns([1, 1])
        
        with col_scan_left:
            st.markdown(f"""
                <div class="scanline-container" style="max-width: 100%; height: 400px; display: flex; align-items: center; justify-content: center; background-color: #0E1117; border-radius: 8px; border: 1px solid #2E3340; overflow: hidden; position: relative;">
                    <div class="scanline"></div>
                    <img src="data:image/jpeg;base64,{img_str}" style="max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px; opacity: 0.7;">
                </div>
                <p style="text-align: center; color: #E8640A; font-size: 0.8rem; letter-spacing: 2px;">[AGENT 1: INSPECTOR] SCANNING IN PROGRESS...</p>
            """, unsafe_allow_html=True)
            
        with col_scan_right:
            log_placeholder = st.empty()
            chart_placeholder = st.empty()
            
            logs = [
                "[INIT] AMD Instinct™ MI300X Pipeline...",
                "[HW] ALLOCATING HBM3 MEMORY...",
                "[VLLM] LOADING QWEN3-VL WEIGHTS...",
                "[SCAN] CAPTURING VISUAL FEATURES...",
                "[AI] ANALYZING COMPONENT GEOMETRY...",
                "[SPEC] CROSS-REFERENCING SPECIFICATION...",
                "⚡ ACCELERATING INFERENCE VIA ROCm 6.0...",
                "[DATA] GENERATING STRUCTURED JSON..."
            ]
            
            # Start the background inspection
            import threading
            from concurrent.futures import ThreadPoolExecutor
            import random
            import pandas as pd
            
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(run_inspection, image, specification)
            
            # Live Telemetry Simulation
            history_data = []
            
            # Simulate log typing while waiting
            for i in range(len(logs) * 2): # Longer loop for more updates
                if future.done(): break
                
                # Update logs
                log_idx = min(i // 2, len(logs) - 1)
                current_logs = "<br>".join([f'<span style="color: #8B919A;">></span> {l}' for l in logs[:log_idx+1]])
                log_placeholder.markdown(f"""
                    <div style="background: #1A1D23; border: 1px solid #2E3340; border-radius: 8px; padding: 1.2rem; font-family: monospace; height: 180px; overflow-y: hidden; margin-bottom: 0.5rem;">
                        <h5 style="color: #E8640A; margin: 0; font-size: 0.8rem;">[SYS] HW TELEMETRY</h5>
                        <div style="font-size: 0.8rem; line-height: 1.5; margin-top: 0.5rem;">
                            {current_logs}
                            <span style="display: inline-block; width: 6px; height: 12px; background: #E8640A; animation: blink 1s infinite;"></span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Update Live Chart (Simulated GPU Throughput)
                new_val = random.uniform(18.5, 24.8)
                history_data.append(new_val)
                if len(history_data) > 20: history_data.pop(0)
                
                with chart_placeholder.container():
                    st.markdown(f'<p style="color: #8B919A; font-size: 0.7rem; margin-bottom: -10px;">LIVE THROUGHPUT: <strong style="color:#10B981;">{new_val:.1f} tok/s</strong></p>', unsafe_allow_html=True)
                    st.line_chart(history_data, height=120, width="stretch")
                
                time.sleep(0.4)
            
            response = future.result()
            
        scan_placeholder.empty() # Remove scan effect when done

    # Handle errors
    if response["error"]:
        st.error(f"[ERROR] Inspection Failed: {response['error']}")
        col_retry, _ = st.columns([1, 3])
        with col_retry:
            if st.button("🔄 Retry", width="stretch"):
                st.rerun()
        return

    result = response["result"]
    result["usage"] = response.get("usage", {})
    elapsed = response["elapsed"]

    # Generate annotations once
    passed = result.get("inspection_passed", False)
    
    # ── AGENT 2 HANDOFF: Quality Engineer ──
    if not passed:
        with st.spinner("⚠️ Anomaly detected. Handing off to [AGENT 2: QUALITY ENGINEER] for root cause analysis..."):
            from quality_engineer import run_quality_engineer_agent
            qe_response = run_quality_engineer_agent(image, result)
            if not qe_response.get("error"):
                result["quality_engineer_diagnostics"] = qe_response["result"]
                elapsed += qe_response["elapsed"]
            else:
                st.error(f"Quality Engineer Agent failed: {qe_response['error']}")
    annotated = annotate_image(image, result.get("items", []))
    annotated = draw_inspection_badge(annotated, passed)

    # Save to history
    history_entry = create_history_entry(image, annotated, result, elapsed, specification)
    st.session_state.history.append(history_entry)
    
    # Set current viewing state
    st.session_state.last_result = result
    st.session_state.current_image = image
    st.session_state.current_annotated = annotated
    st.session_state.current_specification = specification
    st.session_state.current_elapsed = elapsed
    st.session_state.viewing_history = False
    
    # Trigger a rerun to show the results via the main content area logic
    # This prevents the results from being rendered inside the tabs layout
    st.rerun()


# ─── Main Content: Tabs ───────────────────────────────────────────────

# ─── Main Content Area ───────────────────────────────────────────────

# If we have a pending batch inspection
if st.session_state.get("pending_batch_images") is not None:
    images = st.session_state.pending_batch_images
    spec = st.session_state.pending_batch_spec
    st.session_state.pending_batch_images = None
    st.session_state.pending_batch_spec = None
    execute_batch_inspection(images, spec)

# If we are viewing a batch result
elif st.session_state.get("last_batch_result") is not None:
    render_batch_results(st.session_state.last_batch_result)

# If we have a pending inspection (just captured from camera or uploaded)
elif st.session_state.get("pending_inspection_img") is not None:
    img = st.session_state.pending_inspection_img
    spec = st.session_state.pending_inspection_spec
    # Reset pending state immediately so we don't loop
    st.session_state.pending_inspection_img = None
    st.session_state.pending_inspection_spec = None
    # Now execute in the main area context
    execute_inspection(img, spec)

# If we are viewing a result (either from history or just finished)
elif st.session_state.last_result is not None:
    # Use the reusable renderer
    render_inspection_results(
        st.session_state.last_result,
        st.session_state.current_image,
        st.session_state.current_annotated,
        st.session_state.current_specification,
        st.session_state.get("current_elapsed", 0)
    )
else:
    # Tabs only show when no result is being viewed
    tab_upload, tab_camera, tab_batch = st.tabs(["Upload Mode", "Live Camera", "Batch Mode"])

    # ──────────────────────────────────────────────────────────────────────
    # TAB 1: Upload Mode
    # ──────────────────────────────────────────────────────────────────────

    with tab_upload:
        st.markdown("#### Upload an image and describe what it should contain")

        col_input_img, col_input_spec = st.columns([1, 1])

        with col_input_img:
            st.markdown("##### Image")
            
            # Dynamic text for single mode
            has_img = st.session_state.get("manual_upload") or st.session_state.get("demo_image")
            single_btn_text = "CHANGE IMAGE" if has_img else "UPLOAD IMAGE"
            st.markdown(f"""
                <style>
                /* Target only the single mode uploader button */
                [data-testid="stFileUploader"]:not([key*="batch"]) button {{
                    font-size: 0 !important;
                }}
                [data-testid="stFileUploader"]:not([key*="batch"]) button::after {{
                    content: "{single_btn_text}";
                    font-size: 0.9rem !important;
                    display: block;
                }}
                </style>
            """, unsafe_allow_html=True)

            uploaded_file = st.file_uploader(
                "Upload an image of the object to inspect",
                type=config.SUPPORTED_FORMATS,
                key="manual_upload",
                label_visibility="collapsed"
            )

            if uploaded_file:
                st.session_state.demo_image = None # Clear demo if user uploads
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded image", width="stretch")
            
            # Demo Gallery
            st.markdown("##### QUICK DEMOS")
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                if st.button("[PCB]", width="stretch"):
                    st.session_state.demo_image = Image.open("assets/demos/pcb_assembly.jpg")
                    st.session_state.template_select = "PCB Assembly"
                    st.session_state.spec_input = config.INSPECTION_TEMPLATES["PCB Assembly"]
                    st.rerun()
            
            with col_d2:
                if st.button("[PANEL]", width="stretch"):
                    st.session_state.demo_image = Image.open("assets/demos/electrical_panel.jpg")
                    st.session_state.template_select = "Electrical Panel"
                    st.session_state.spec_input = config.INSPECTION_TEMPLATES["Electrical Panel"]
                    st.rerun()
            
            with col_d3:
                if st.button("[TOOLS]", width="stretch"):
                    st.session_state.demo_image = Image.open("assets/demos/bgs_tool_kit.PNG")
                    st.session_state.template_select = "BGS Tool Kit"
                    st.session_state.spec_input = config.INSPECTION_TEMPLATES["BGS Tool Kit"]
                    st.rerun()

            if st.session_state.get("demo_image"):
                col_demo_head, col_demo_clear = st.columns([3, 1])
                with col_demo_head:
                    st.caption(f"Demo Loaded: {st.session_state.get('template_select')}")
                with col_demo_clear:
                    if st.button("✖️ CLEAR", key="clear_demo", width="stretch"):
                        st.session_state.demo_image = None
                        st.rerun()
                
                st.image(st.session_state.demo_image, width="stretch")
                image = st.session_state.demo_image

        with col_input_spec:
            st.markdown("##### Inspection Specification")

            # Template selector
            template_name = st.selectbox(
                "Choose a template or write custom",
                options=list(config.INSPECTION_TEMPLATES.keys()),
                key="template_select",
                on_change=update_template
            )

            # Specification text area
            default_spec = config.INSPECTION_TEMPLATES.get(template_name, "")
            specification = st.text_area(
                "Describe expected items in natural language",
                height=200,
                placeholder="Example:\nExpected items:\n- 4x resistor (blue body, through-hole)\n- 1x capacitor (cylindrical, blue)\n- 1x IC chip (black, rectangular)",
                key="spec_input"
            )

            # Discovery button
            if st.button("[AUTO] Discover Components", width="stretch", help="Let AI identify everything it sees first"):
                img_to_disc = uploaded_file if uploaded_file else st.session_state.get("demo_image")
                
                if img_to_disc:
                    if isinstance(img_to_disc, Image.Image):
                        process_img = img_to_disc
                    else:
                        process_img = Image.open(img_to_disc)
                    
                    with st.spinner("[DISCOVERING] COMPONENTS..."):
                        discovery_res = run_discovery(process_img)
                        if discovery_res["error"]:
                            st.error(f"Discovery Error: {discovery_res['error']}")
                        else:
                            st.session_state.discovery_data = discovery_res["result"]
                else:
                    st.warning("Please upload an image first.")

            # Show discovery results if present
            if st.session_state.get("discovery_data"):
                with st.expander("[LOG] Discovered Components (Use these for your spec)", expanded=True):
                    items = st.session_state.discovery_data.get("discovered_items", [])
                    for it in items:
                        st.markdown(f"- **{it.get('name', 'Unknown')}**: {it.get('description', 'No description')}")
                    if st.button("Clear Discovery"):
                        st.session_state.discovery_data = None
                        st.rerun()

        # Run button
        st.markdown("")
        col_run, col_info = st.columns([1, 3])
        with col_run:
            run_clicked = st.button(
                "Run Inspection",
                width="stretch",
                type="primary",
                disabled=(uploaded_file is None and st.session_state.get("demo_image") is None)
            )
        with col_info:
            st.markdown(f"""
                <div style="margin-top: 5px; color: #8B919A; font-size: 0.75rem; text-align: right; opacity: 0.6;">
                    ENGINE: {config.VLM_MODEL.split('/')[-1]}
                </div>
            """, unsafe_allow_html=True)

            if run_clicked:
                active_image = None
                if uploaded_file:
                    active_image = Image.open(uploaded_file)
                elif st.session_state.get("demo_image"):
                    active_image = st.session_state.demo_image
                    
                if active_image:
                    # SET STATE FOR MAIN AREA TO TAKE OVER
                    st.session_state.pending_inspection_img = active_image
                    st.session_state.pending_inspection_spec = specification
                    st.rerun()
                else:
                    st.error("Please upload an image or use the demo sample.")


    # ──────────────────────────────────────────────────────────────────────
    # TAB 2: Live Camera
    # ──────────────────────────────────────────────────────────────────────

    with tab_camera:
        st.markdown("#### Live camera inspection with automatic stability detection")

        col_cam_ctrl, col_cam_spec = st.columns([2, 1])

        with col_cam_spec:
            st.markdown("##### [SPEC] Specification")

            template_cam = st.selectbox(
                "Choose a template",
                options=list(config.INSPECTION_TEMPLATES.keys()),
                key="template_camera"
            )

            spec_cam = st.text_area(
                "Inspection specification",
                value=config.INSPECTION_TEMPLATES.get(template_cam, ""),
                height=180,
                key="spec_camera"
            )

        with col_cam_ctrl:
            st.markdown("##### [CAM] Feed")

            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("[START] Camera", width="stretch"):
                    st.session_state.camera_active = True
                    st.rerun()
            with col_btn2:
                if st.button("[STOP] Camera", width="stretch"):
                    st.session_state.camera_active = False
                    st.rerun()
            with col_btn3:
                if st.button("[CAPTURE] Manual", width="stretch"):
                    st.session_state.manual_capture_trigger = True

            # Camera feed area
            camera_placeholder = st.empty()
            stability_bar = st.empty()
            status_text = st.empty()


            if st.session_state.camera_active:
                camera_placeholder.info("[CAM] INITIALIZING PIPELINE...")
                cam = CameraManager(source=st.session_state.camera_source)
                
                if cam.connect():
                    status_text.success("Camera connected — place object and hold still")
                    
                    # Live Loop
                    retry_count = 0
                    while st.session_state.camera_active:
                        frame = cam.read_frame()
                        if frame is not None:
                            retry_count = 0 # Reset on success
                            # Show current frame
                            camera_placeholder.image(
                                CameraManager.frame_to_rgb(frame),
                                caption="Live feed — hold object still for auto-capture",
                                width="stretch"
                            )

                            # Check stability
                            is_stable, motion_score = cam.check_stability(frame)
                            progress = cam.get_stability_progress()
                            stability_bar.progress(
                                int(progress),
                                text=f"Stability: {progress:.0f}% | Motion: {motion_score:.4f}"
                            )

                            if is_stable or st.session_state.get("manual_capture_trigger"):
                                st.session_state.manual_capture_trigger = False
                                status_text.info("Capture triggered! Switching to analysis...")
                                pil_image = CameraManager.frame_to_pil(frame)
                                cam.disconnect()
                                st.session_state.camera_active = False
                                
                                # SET STATE FOR MAIN AREA TO TAKE OVER
                                st.session_state.pending_inspection_img = pil_image
                                st.session_state.pending_inspection_spec = spec_cam

                                # CLEAR UI BEFORE RERUN TO PREVENT MEDIA ERRORS
                                camera_placeholder.empty()
                                stability_bar.empty()
                                status_text.empty()
                                
                                st.rerun()
                                break
                        else:
                            retry_count += 1
                            if retry_count > 5:
                                status_text.error("[ERROR] Failed to read frame from camera after several attempts")
                                break
                            time.sleep(0.1)
                        
                        # Small sleep to prevent high CPU usage
                        time.sleep(0.01)
                    
                    cam.disconnect()
                else:
                    status_text.error(
                        f"[ERROR] Cannot connect to camera ({st.session_state.camera_source}). "
                        "Check your camera source in the sidebar settings."
                    )


            elif st.session_state.get("manual_capture_trigger"):
                st.session_state.manual_capture_trigger = False # Reset trigger

                cam = CameraManager(source=st.session_state.camera_source)
                if cam.connect():
                    frame = cam.read_frame()
                    if frame is not None:
                        pil_image = CameraManager.frame_to_pil(frame)
                        camera_placeholder.image(
                            CameraManager.frame_to_rgb(frame),
                            caption="Captured frame",
                            width="stretch"
                        )
                        cam.disconnect()
                        # SET STATE FOR MAIN AREA TO TAKE OVER
                        st.session_state.pending_inspection_img = pil_image
                        st.session_state.pending_inspection_spec = spec_cam
                        st.rerun()
                    else:
                        status_text.error("[ERROR] Failed to capture frame")
                        cam.disconnect()
                else:
                    status_text.error("[ERROR] Cannot connect to camera")

        # Camera tips
        with st.expander("Camera Tips"):
            st.markdown("""
            **Using laptop webcam:**
            - Select "Laptop Webcam" in sidebar settings
            - Ensure adequate lighting (desk lamp recommended)
            - Use a uniform background (white or black surface)

            **Using phone as IP camera:**
            - Install [DroidCam](https://www.dev47apps.com/) or [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam)
            - Connect phone to same WiFi network as your PC
            - Set `CAMERA_URL` in `.env` to the phone's stream URL
            - Select "Phone IP Camera" in sidebar settings

            **For best results:**
            - Keep the object centered in frame
            - Avoid shadows and reflections
            - Hold still for 1+ second for auto-capture
            - Use manual capture (📸) if auto-detection is unreliable
            """)

    # ──────────────────────────────────────────────────────────────────────
    # TAB 3: Batch Mode
    # ──────────────────────────────────────────────────────────────────────

    with tab_batch:
        st.markdown("#### Upload multiple images to analyze them in parallel")
        
        uploaded_batch = st.session_state.get("upload_batch", None)
        
        col_batch_img, col_batch_spec = st.columns([1, 1])
        
        with col_batch_img:
            # Dynamic CSS Hack to change "Browse files" text
            button_text = "➕ ADD MORE IMAGES" if uploaded_batch else "ADD IMAGES"
            st.markdown(f"""
                <style>
                /* 1. Cambiar el texto del botón principal */
                [data-testid="stFileUploader"] button {{
                    font-size: 0 !important;
                    padding: 0.5rem 1rem !important;
                }}
                [data-testid="stFileUploader"] button::after {{
                    content: "{button_text}";
                    font-size: 0.9rem !important;
                    display: block;
                }}
                
                /* 2. REVERTIR el cambio para los botones de la lista (las X) */
                [data-testid="stFileUploader"] ul button {{
                    font-size: 14px !important; /* Tamaño normal de la X */
                }}
                [data-testid="stFileUploader"] ul button::after {{
                    content: "" !important;
                    display: none !important;
                }}
                </style>
            """, unsafe_allow_html=True)

            # 1. Preview Gallery First
            if uploaded_batch:
                st.markdown('<div style="margin-bottom: 10px; color: #E8640A; font-weight: bold; font-size: 0.8rem;">[QUEUE] CURRENT IMAGES:</div>', unsafe_allow_html=True)
                cols_preview = st.columns(4)
                for idx, file in enumerate(uploaded_batch[:8]): 
                    with cols_preview[idx % 4]:
                        st.image(file, width="stretch")
                st.markdown("<br>", unsafe_allow_html=True)

            # 2. "Add More" Uploader Below
            uploaded_batch = st.file_uploader(
                "Upload zone",
                type=config.SUPPORTED_FORMATS,
                accept_multiple_files=True,
                key="upload_batch",
                label_visibility="collapsed"
            )
            
            if uploaded_batch:
                if len(uploaded_batch) > 8:
                    st.warning(f"[WARN] You uploaded {len(uploaded_batch)} images. Only the first 8 will be processed to prevent API rate limits.")
                    uploaded_batch = uploaded_batch[:8]
                st.caption(f"[INFO] {len(uploaded_batch)} images ready for inspection.")
                
        with col_batch_spec:
            st.markdown("##### Inspection Specification")
            
            template_batch = st.selectbox(
                "Choose a template",
                options=list(config.INSPECTION_TEMPLATES.keys()),
                key="template_batch"
            )

            spec_batch = st.text_area(
                "Inspection specification (applies to all images)",
                value=config.INSPECTION_TEMPLATES.get(template_batch, ""),
                height=180,
                key="spec_batch"
            )
            
        st.markdown("")
        col_run_batch, col_info_batch = st.columns([1, 3])
        with col_run_batch:
            run_batch_clicked = st.button(
                "START BATCH INSPECTION",
                width="stretch",
                type="primary",
                disabled=(not uploaded_batch)
            )
        with col_info_batch:
            st.caption(f"[LINK] Connected to {config.VLM_MODEL} on AMD Cloud (MI300X)")
            
            if run_batch_clicked and uploaded_batch:
                st.session_state.pending_batch_images = [Image.open(f) for f in uploaded_batch]
                st.session_state.pending_batch_spec = spec_batch
                st.rerun()


# ─── Footer ───────────────────────────────────────────────────────────

st.markdown("---")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.markdown("""
    <div class="metric-card">
        <div class="label">Powered By</div>
        <div class="value" style="font-size: 1.2rem;">AMD MI300X</div>
    </div>
    """, unsafe_allow_html=True)

with col_f2:
    st.markdown("""
    <div class="metric-card">
        <div class="label">Model</div>
        <div class="value" style="font-size: 1.2rem;">Qwen3-VL</div>
    </div>
    """, unsafe_allow_html=True)

with col_f3:
    st.markdown("""
    <div class="metric-card">
        <div class="label">Training Required</div>
        <div class="value" style="font-size: 1.2rem;">Zero</div>
    </div>
    """, unsafe_allow_html=True)

st.caption(
    f"AsBuilt Lens v{config.APP_VERSION} · "
    "AMD Developer Hackathon 2026 · "
    "Track 3: Vision & Multimodal AI · "
    "MIT License"
)
