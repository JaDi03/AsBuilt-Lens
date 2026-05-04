<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo_dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo1.PNG">
    <img alt="AsBuilt Lens Logo" src="assets/logo1.PNG" width="320">
  </picture>
</p>

<h3 align="center">Describe what should exist. The AI verifies it visually.</h3>

<p align="center">
  <img src="https://img.shields.io/badge/AMD-MI300X-ED1C24?style=for-the-badge&logo=amd&logoColor=white" alt="AMD MI300X"/>
  <img src="https://img.shields.io/badge/Model-Qwen3--VL-orange?style=for-the-badge" alt="Qwen3-VL"/>
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License"/>
</p>

---

## What is AsBuilt Lens?

**AsBuilt Lens** is a zero-shot visual inspection platform built for the **AMD Developer Hackathon 2026 — Track 3: Vision & Multimodal AI**.

It uses the **Qwen3-VL** multimodal model running on **AMD Instinct MI300X** GPUs (via vLLM) to verify that physical objects match a natural-language specification — with no training data, no fine-tuning, and no custom datasets required.

Point a camera at a PCB, a toolbox, or a packaged product. Describe what should be there. The AI tells you what's present, what's missing, and what looks wrong.

---

## Key Features

- **Zero-Shot Inspection** — No ML training required. Write a spec in plain English, run the inspection.
- **Live Camera Mode** — Connect your laptop webcam or any IP camera (DroidCam, IP Webcam). Automatic motion-stability detection triggers capture when the object is held still.
- **Upload Mode** — Upload any image (JPG, PNG, WEBP, BMP) for offline or batch inspection.
- **Structured JSON Results** — Every inspection returns a structured report: item-by-item status, detected counts, confidence scores, and a human-readable summary.
- **Annotated Output Image** — Results are overlaid directly on the inspected image with color-coded bounding indicators and a PASS/FAIL badge.
- **Inspection History** — Every run is logged in the sidebar with timestamp, pass rate, and specification.
- **Built-in Templates** — Comes with ready-to-use inspection templates for PCB Assembly, Tool Kits, Electrical Panels, and Packaging Verification.
- **Demo Mode** — One-click demo with a pre-loaded PCB sample image so judges can evaluate without any hardware.

---

## Architecture

```
AsBuilt-Lens/
├── app/
│   ├── app.py              # Main Streamlit UI & application loop
│   ├── config.py           # Environment variable loading & constants
│   ├── inspector.py        # VLM API calls, JSON parsing, retry logic
│   ├── camera.py           # Webcam/IP camera management & stability detection
│   ├── utils.py            # Image annotation, formatting utilities
│   └── prompts/
│       └── inspection_prompt.txt  # Structured prompt template for Qwen3-VL
├── assets/
│   ├── logo_dark.png       # UI logo (dark mode optimized)
│   ├── demo_pcb.jpg        # Demo image for one-click testing
│   ├── cover.png           # Hackathon submission cover (16:9)
│   └── og-image.png        # Social sharing preview image
├── .streamlit/
│   └── config.toml         # Streamlit theme (Phoenix dark mode)
├── .env.example            # Environment variable template
├── requirements.txt
└── README.md
```

---

## How It Works

```
User writes specification
        │
        ▼
  Image captured (upload or live camera)
        │
        ▼
  Image resized & encoded as base64 JPEG
        │
        ▼
  Prompt built: specification injected into structured template
        │
        ▼
  POST → AMD MI300X (vLLM → Qwen3-VL)
        │
        ▼
  JSON parsed: items[], inspection_passed, summary
        │
        ▼
  Results rendered: annotated image + item cards + PASS/FAIL badge
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/JaDi03/AsBuilt-Lens.git
cd AsBuilt-Lens
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your environment

```bash
cp .env.example .env
```

Edit `.env` with your AMD Developer Cloud endpoint:

```env
# AMD Developer Cloud
AMD_API_URL=http://your-mi300x-ip:8000/v1
AMD_API_KEY=your_api_key_if_needed
VLM_MODEL=Qwen/Qwen3-VL-32B-Instruct

# Camera (optional — only needed for Live Camera mode)
CAMERA_URL=http://192.168.1.100:8080/video

# Tuning
STABILITY_THRESHOLD=0.02
STABILITY_FRAMES=30
MAX_IMAGE_SIZE=720
```

### 4. Run the application

```bash
python -m streamlit run app/app.py
```

Open your browser at `http://localhost:8501`.

---

## Live Camera Setup

**Option A — Laptop Webcam**
1. Select **"Laptop Webcam"** in the sidebar.
2. Click **▶️ Start Camera**.
3. Hold your object steady. The stability bar fills up and auto-captures.

**Option B — Phone as IP Camera**
1. Install [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) (Android) or [DroidCam](https://www.dev47apps.com/).
2. Connect your phone to the same Wi-Fi network as your PC.
3. Set `CAMERA_URL` in your `.env` to the stream URL shown in the app (e.g. `http://192.168.1.78:8080/video`).
4. Select **"Phone IP Camera"** in the sidebar and click **▶️ Start Camera**.

---

## Inspection Templates

| Template | Use Case |
|---|---|
| **PCB Assembly** | Verify resistors, capacitors, IC chips, LEDs, oscillators |
| **Packaging Verification** | Check product, manual, warranty card, accessories |
| **Tool Kit Inspection** | Verify presence of specific hand tools |
| **Electrical Panel** | Check breakers, bus bars, labels, wiring safety |
| **Custom Specification** | Write your own natural-language checklist |

---

## Example Result

```json
{
  "inspection_passed": true,
  "items": [
    { "id": "resistor", "expected_count": 4, "detected_count": 4, "status": "present", "confidence": 94 },
    { "id": "electrolytic_capacitor", "expected_count": 1, "detected_count": 1, "status": "present", "confidence": 91 },
    { "id": "ic_chip", "expected_count": 1, "detected_count": 1, "status": "present", "confidence": 97 },
    { "id": "led", "expected_count": 1, "detected_count": 0, "status": "missing", "confidence": 88, "note": "No LED visible in expected location." }
  ],
  "summary": "3 of 4 items verified. LED component not detected — recheck position D1.",
  "notes": ""
}
```

---

## Tech Stack

| Component | Technology |
|---|---|
| **GPU Compute** | AMD Instinct MI300X |
| **Inference Engine** | vLLM (ROCm) |
| **Vision Model** | Qwen3-VL-32B-Instruct |
| **API Protocol** | OpenAI-compatible REST |
| **Frontend** | Streamlit 1.30+ |
| **Computer Vision** | OpenCV 4.8+ |
| **Image Processing** | Pillow 10+ |
| **Runtime** | Python 3.10+ |

---

## Hackathon Submission

- **Event**: AMD Developer Hackathon 2026
- **Track**: Track 3 — Vision & Multimodal AI
- **Team**: AsBuilt Lens Team
- **Model**: Qwen3-VL-32B-Instruct on AMD MI300X via ROCm + vLLM

---

## License

MIT License — see [LICENSE](LICENSE) for details.
