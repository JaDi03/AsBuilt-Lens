"""
AsBuilt Lens — Main Streamlit Application
Zero-shot visual inspection powered by AMD MI300X + Qwen3-VL.
"""

import streamlit as st
import time
import numpy as np
from PIL import Image

import config
from inspector import run_inspection, run_mock_inspection
from camera import CameraManager, test_camera_connection
from utils import (
    annotate_image, draw_inspection_badge, format_elapsed_time,
    get_status_icon, get_status_color, get_status_bg_color,
    calculate_pass_rate, create_history_entry, COLORS
)

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

    /* Main header styling - Flush to top */
    .main-header {
        background: #22262E;
        border-bottom: 2px solid #E8640A;
        padding: 1rem 2.5rem;
        margin: 0 -5rem 1.5rem -5rem;
        text-align: center;
    }
    .main-header p {
        color: #8B919A;
        font-size: 0.95rem;
        font-weight: 300;
        margin-bottom: 0.75rem;
        margin-top: 0.5rem;
    }
    .logo-img {
        max-width: 280px;
        margin-bottom: 0rem;
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

    /* Timer chip */
    .timer-chip {
        display: inline-block;
        background: #22262E;
        border: 1px solid #2E3340;
        border-radius: 4px;
        padding: 0.3rem 0.8rem;
        color: #8B919A;
        font-size: 0.85rem;
        margin-bottom: 0.75rem;
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
        "last_result": None,
        "camera_active": False,
        "manual_capture_trigger": False,
        "demo_image": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
    {logo_html}
    <p>{config.APP_TAGLINE}</p>
    <div>
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

    # ── Settings ──
    st.markdown("#### Settings")

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
            status_emoji = "✅" if entry["passed"] else "❌"
            st.markdown(f"""
            <div class="history-entry {status_class}">
                <strong>{status_emoji} #{len(st.session_state.history) - i}</strong>
                &nbsp;|&nbsp; {entry['passed_count']}/{entry['total_count']} items
                &nbsp;|&nbsp; {format_elapsed_time(entry['elapsed'])}
                <br><small style="color: #64748B;">{entry['timestamp']} — {entry['specification'][:50]}</small>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️ Clear History", width="stretch"):
            st.session_state.history = []
            st.rerun()

    st.divider()

    # ── About ──
    st.markdown("#### ℹ️ About")
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


# ─── Inspection Function ──────────────────────────────────────────────

def execute_inspection(image: Image.Image, specification: str):
    """Run inspection and display results."""
    if not specification.strip():
        st.error("⚠️ Please enter an Inspection Specification before running.")
        return

    # Run inspection
    with st.spinner("🔍 Analyzing on AMD Cloud..."):
        response = run_inspection(image, specification)

    # Handle errors
    if response["error"]:
        st.error(f"❌ Inspection Failed: {response['error']}")
        col_retry, _ = st.columns([1, 3])
        with col_retry:
            if st.button("🔄 Retry", width="stretch"):
                st.rerun()
        return

    result = response["result"]
    elapsed = response["elapsed"]

    # ── Display Results ──
    st.markdown("---")

    # Timer
    st.markdown(
        f'<div class="timer-chip">⏱️ Inspection completed in {format_elapsed_time(elapsed)}</div>',
        unsafe_allow_html=True
    )

    # Pass/Fail Badge
    passed = result.get("inspection_passed", False)
    passed_count, total_count = calculate_pass_rate(result.get("items", []))

    if passed:
        st.markdown(
            f'<div class="status-pass">✅ INSPECTION PASSED — {passed_count}/{total_count} items verified</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="status-fail">❌ INSPECTION FAILED — {passed_count}/{total_count} items verified</div>',
            unsafe_allow_html=True
        )

    # Annotated image + item details
    col_img, col_details = st.columns([1, 1])

    with col_img:
        st.markdown("##### 🖼️ Annotated Image")
        annotated = annotate_image(image, result.get("items", []))
        annotated = draw_inspection_badge(annotated, passed)
        st.image(annotated, width="stretch")

    with col_details:
        st.markdown("##### 📊 Item Details")

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
    st.markdown("##### 📝 Summary")
    st.info(result.get("summary", "No summary available."))

    if result.get("notes"):
        st.caption(f"📋 Notes: {result['notes']}")

    # Save to history
    history_entry = create_history_entry(image, result, elapsed, specification)
    st.session_state.history.append(history_entry)
    st.session_state.last_result = result


# ─── Main Content: Tabs ───────────────────────────────────────────────

tab_upload, tab_camera = st.tabs(["Upload Mode", "Live Camera"])

# ──────────────────────────────────────────────────────────────────────
# TAB 1: Upload Mode
# ──────────────────────────────────────────────────────────────────────

with tab_upload:
    st.markdown("#### Upload an image and describe what it should contain")

    col_input_img, col_input_spec = st.columns([1, 1])

    with col_input_img:
        st.markdown("##### Image")
        uploaded_file = st.file_uploader(
            "Upload an image of the object to inspect",
            type=config.SUPPORTED_FORMATS,
            key="upload_image",
            help="Supported formats: JPG, JPEG, PNG, BMP, WEBP"
        )

        if uploaded_file:
            st.session_state.demo_image = None # Clear demo if user uploads
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded image", width="stretch")
        
        # Demo button
        if st.button("🖼️ Use Demo PCB Sample", width="stretch", help="Load a pre-configured sample image for testing"):
            st.session_state.demo_image = Image.open("assets/demo_pcb.jpg")
            st.session_state.template_select = "PCB Assembly"
            st.rerun()

        if st.session_state.get("demo_image"):
            st.image(st.session_state.demo_image, caption="Demo PCB Sample Loaded", width="stretch")
            image = st.session_state.demo_image

    with col_input_spec:
        st.markdown("##### Inspection Specification")

        # Template selector
        template_name = st.selectbox(
            "Choose a template or write custom",
            options=list(config.INSPECTION_TEMPLATES.keys()),
            key="template_select"
        )

        # Specification text area
        default_spec = config.INSPECTION_TEMPLATES.get(template_name, "")
        specification = st.text_area(
            "Describe expected items in natural language",
            value=default_spec,
            height=200,
            placeholder="Example:\nExpected items:\n- 4x resistor (blue body, through-hole)\n- 1x capacitor (cylindrical, blue)\n- 1x IC chip (black, rectangular)",
            key="spec_input"
        )

    # Run button
    st.markdown("")
    col_run, col_info = st.columns([1, 3])
    with col_run:
        run_clicked = st.button(
            "Run Inspection",
            width="stretch",
            type="primary",
            disabled=uploaded_file is None
        )
    with col_info:
        st.caption(f"🔗 Connected to {config.VLM_MODEL} on AMD Cloud (MI300X)")

    if run_clicked:
        active_image = None
        if uploaded_file:
            active_image = Image.open(uploaded_file)
        elif st.session_state.get("demo_image"):
            active_image = st.session_state.demo_image
            
        if active_image:
            execute_inspection(active_image, specification)
        else:
            st.error("Please upload an image or use the demo sample.")


# ──────────────────────────────────────────────────────────────────────
# TAB 2: Live Camera
# ──────────────────────────────────────────────────────────────────────

with tab_camera:
    st.markdown("#### Live camera inspection with automatic stability detection")

    col_cam_ctrl, col_cam_spec = st.columns([2, 1])

    with col_cam_spec:
        st.markdown("##### 📋 Specification")

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
        st.markdown("##### 🎥 Camera Feed")

        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("▶️ Start Camera", width="stretch"):
                st.session_state.camera_active = True
                st.rerun()
        with col_btn2:
            if st.button("⏹️ Stop Camera", width="stretch"):
                st.session_state.camera_active = False
                st.rerun()
        with col_btn3:
            if st.button("📸 Manual Capture", width="stretch"):
                st.session_state.manual_capture_trigger = True

        # Camera feed area
        camera_placeholder = st.empty()
        stability_bar = st.empty()
        status_text = st.empty()


        if st.session_state.camera_active:
            cam = CameraManager(source=st.session_state.camera_source)
            if cam.connect():
                status_text.success("Camera connected — place object and hold still")
                
                # Live Loop
                while st.session_state.camera_active:
                    frame = cam.read_frame()
                    if frame is not None:
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
                            status_text.info("Capture triggered! Analyzing...")
                            pil_image = CameraManager.frame_to_pil(frame)
                            cam.disconnect()
                            st.session_state.camera_active = False
                            execute_inspection(pil_image, spec_cam)
                            st.rerun()
                            break
                    else:
                        status_text.error("❌ Failed to read frame from camera")
                        break
                    
                    # Small sleep to prevent high CPU usage
                    time.sleep(0.01)
                
                cam.disconnect()
            else:
                status_text.error(
                    f"❌ Cannot connect to camera ({st.session_state.camera_source}). "
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
                    execute_inspection(pil_image, spec_cam)
                else:
                    status_text.error("❌ Failed to capture frame")
                    cam.disconnect()
            else:
                status_text.error("❌ Cannot connect to camera")

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
