"""
Brain Tumor MRI Classifier — Streamlit Web Prototype (v1)

Run with:  streamlit run app.py

The app implements the three confidence states from the PRD (§6):
  - State A: Tumor Detected       (red card, confidence ≥ 90%)
  - State B: No Tumor Detected    (green card, confidence ≥ 90%)
  - State C: Manual Review        (amber card, confidence < 90%)
  - State D: OOD Rejected         (amber card, not a brain MRI)
  - State E: Error                (red border, bad file)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import streamlit as st
import yaml
from PIL import Image

# ---- Logging setup (writes to logs/inference.log) ----
logging.basicConfig(
    filename="logs/inference.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)
os.makedirs("logs", exist_ok=True)

# ---- Config ----
_CONFIG_PATH = Path("config.yaml")
with open(_CONFIG_PATH) as f:
    CFG = yaml.safe_load(f)

CLASSIFIER_PATH = Path(CFG["paths"]["models_dir"]) / "classifier_best.pt"
OOD_MODEL_PATH = Path(CFG["ood"]["model_path"])
HIGH_CONF = CFG["inference"]["high_confidence_threshold"]

# ---- Streamlit page config ----
st.set_page_config(
    page_title="Brain Tumor MRI Classifier",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---- Custom CSS for result cards ----
st.markdown("""
<style>
  .card-tumor {
    background: #fde8e8; border-left: 6px solid #e53e3e;
    padding: 1.2rem 1.5rem; border-radius: 8px; margin: 1rem 0;
  }
  .card-clear {
    background: #e8f5e9; border-left: 6px solid #2e7d32;
    padding: 1.2rem 1.5rem; border-radius: 8px; margin: 1rem 0;
  }
  .card-uncertain {
    background: #fff8e1; border-left: 6px solid #f59e0b;
    padding: 1.2rem 1.5rem; border-radius: 8px; margin: 1rem 0;
  }
  .card-error {
    background: #f3f4f6; border-left: 6px solid #9ca3af;
    padding: 1.2rem 1.5rem; border-radius: 8px; margin: 1rem 0;
  }
  .disclaimer {
    font-size: 0.78rem; color: #6b7280; margin-top: 0.5rem;
  }
  .prob-table { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


# ---- Pipeline loader (cached — model loaded only once per session) ----
@st.cache_resource(show_spinner="Loading AI model…")
def get_pipeline():
    """
    Load the inference pipeline once and cache it for the session.
    st.cache_resource means this function only runs on the first request
    and the pipeline object is reused for all subsequent uploads.
    """
    if not CLASSIFIER_PATH.exists():
        return None  # Model not trained yet — show friendly message

    from src.inference.predict import InferencePipeline
    ood_path = OOD_MODEL_PATH if OOD_MODEL_PATH.exists() else None
    return InferencePipeline(
        classifier_path=CLASSIFIER_PATH,
        ood_model_path=ood_path,
        device="cpu",
    )


# ---- UI ----
def main() -> None:
    st.title("🧠 Brain Tumor MRI Classifier")
    st.markdown(
        "Upload a **2D brain MRI slice** (JPG or PNG). "
        "The AI will analyze it and tell you whether a tumor is likely present."
    )

    _render_disclaimer_banner()

    pipeline = get_pipeline()
    if pipeline is None:
        st.warning(
            "⚙️ Model not found. Please run `notebooks/02_training.ipynb` on Google Colab "
            "to train the model, then place `classifier_best.pt` in the `models/` folder."
        )
        return

    # File uploader
    uploaded_file = st.file_uploader(
        "Drop your MRI image here or click to browse",
        type=["jpg", "jpeg", "png"],
        help="Accepted formats: JPG, JPEG, PNG. Maximum file size: 10 MB.",
    )

    if uploaded_file is None:
        _render_empty_state()
        return

    # File size check (10 MB limit)
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("File is too large (max 10 MB). Please compress the image and try again.")
        return

    # Analyse button
    if st.button("🔍 Analyze", type="primary", use_container_width=True):
        _run_analysis(pipeline, uploaded_file)


def _run_analysis(pipeline, uploaded_file) -> None:
    """Run the full pipeline and render the result card."""
    with st.spinner("Analyzing MRI image…"):
        pil_image = Image.open(uploaded_file).convert("RGB")
        result = pipeline.run(pil_image)

    st.markdown(f"<small>⏱ Analysis completed in {result.latency_ms:.0f} ms</small>", unsafe_allow_html=True)
    st.divider()

    if result.state == "OOD_REJECTED":
        _render_ood_rejection(result)
    elif result.state == "ERROR":
        _render_error(result)
    elif result.state == "HIGH_CONFIDENCE_TUMOR":
        _render_tumor_detected(result)
    elif result.state == "HIGH_CONFIDENCE_CLEAR":
        _render_no_tumor(result)
    elif result.state == "UNCERTAIN":
        _render_uncertain(result)


def _render_tumor_detected(result) -> None:
    st.markdown(
        f'<div class="card-tumor">'
        f'<h3>⚠️ Tumor Detected</h3>'
        f'<p><strong>Confidence: {result.confidence * 100:.1f}%</strong></p>'
        f'<p class="disclaimer">Recommend immediate clinical review. '
        f'This result is a screening aid only — it does not replace a qualified radiologist\'s diagnosis.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    _render_images(result)
    _render_raw_probabilities(result)


def _render_no_tumor(result) -> None:
    st.markdown(
        f'<div class="card-clear">'
        f'<h3>✅ No Tumor Detected</h3>'
        f'<p><strong>Confidence: {result.confidence * 100:.1f}%</strong></p>'
        f'<p class="disclaimer">Routine follow-up recommended per clinical protocol. '
        f'This result is a screening aid only — it does not replace clinical judgment.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    _render_images(result)
    _render_raw_probabilities(result)


def _render_uncertain(result) -> None:
    st.markdown(
        f'<div class="card-uncertain">'
        f'<h3>⚠️ Uncertain Result — Manual Review Required</h3>'
        f'<p>The model\'s confidence is below the {HIGH_CONF * 100:.0f}% clinical safety threshold.</p>'
        f'<p class="disclaimer">A qualified radiologist must review this scan. '
        f'Do not rely on this result for clinical decisions.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # Show original image but NO Grad-CAM (model attention is unreliable when uncertain)
    if result.original_image:
        st.image(result.original_image, caption="Uploaded MRI", use_container_width=True)
    _render_raw_probabilities(result)


def _render_ood_rejection(result) -> None:
    st.markdown(
        '<div class="card-uncertain">'
        '<h3>⚠️ Not a Brain MRI</h3>'
        f'<p>{result.error_message}</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_error(result) -> None:
    st.markdown(
        f'<div class="card-error">'
        f'<h3>❌ Could Not Process Image</h3>'
        f'<p>{result.error_message}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_images(result) -> None:
    """Show original MRI and Grad-CAM overlay side by side."""
    if result.original_image is None:
        return

    if result.gradcam_overlay is not None:
        show_overlay = st.checkbox("Show Grad-CAM heatmap overlay", value=True)
        col1, col2 = st.columns(2)
        with col1:
            st.image(result.original_image, caption="Original MRI", use_container_width=True)
        with col2:
            if show_overlay:
                st.image(result.gradcam_overlay, caption="AI Focus Map (Grad-CAM)", use_container_width=True)
                st.caption(
                    "🔴 Red = high model attention · 🔵 Blue = low attention. "
                    "This is not a clinical segmentation — it shows where the model looked, not a confirmed tumor boundary."
                )
            else:
                st.info("Enable the checkbox above to view the heatmap overlay.")
    else:
        st.image(result.original_image, caption="Uploaded MRI", use_container_width=True)


def _render_raw_probabilities(result) -> None:
    """Always show raw probabilities so the doctor can see the full picture."""
    if result.tumor_probability is None:
        return
    with st.expander("Raw model probabilities"):
        col1, col2 = st.columns(2)
        col1.metric("Tumor", f"{result.tumor_probability * 100:.1f}%")
        col2.metric("No Tumor", f"{result.no_tumor_probability * 100:.1f}%")
        st.caption(
            f"A result is shown as decisive only when one class reaches "
            f"≥{HIGH_CONF * 100:.0f}% confidence."
        )


def _render_disclaimer_banner() -> None:
    st.info(
        "**⚕️ Medical Disclaimer:** This tool is a research prototype intended for "
        "academic demonstration only. It has **not** been clinically validated and "
        "**must not** be used for actual patient diagnosis. Always consult a qualified radiologist.",
        icon="ℹ️",
    )


def _render_empty_state() -> None:
    st.markdown("---")
    st.markdown(
        "#### How it works\n"
        "1. Upload a 2D brain MRI slice (axial/coronal/sagittal plane)\n"
        "2. Click **Analyze**\n"
        "3. Receive a classification result with confidence score and AI focus map\n\n"
        "The model flags any result below **90% confidence** for manual review — "
        "it will never make a guess it is not confident about."
    )


if __name__ == "__main__":
    main()
