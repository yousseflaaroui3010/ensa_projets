"""
FastAPI inference server for the Brain Tumor MRI Classifier.

Wraps the existing InferencePipeline so the HTML frontend uses the real model
instead of a random number generator.

Run with:
    uvicorn api_server:app --reload --port 8000

Then open 'Brain Tumor MRI Classifier.html' in your browser and upload any MRI.
"""

from __future__ import annotations

import base64
import io
import logging
import os
from pathlib import Path

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

# ── Logging ───────────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/api.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
_CONFIG_PATH = Path("config.yaml")
with open(_CONFIG_PATH) as _f:
    CFG = yaml.safe_load(_f)

CLASSIFIER_PATH = Path(CFG["paths"]["models_dir"]) / "classifier_best.pt"
OOD_MODEL_PATH  = Path(CFG["ood"]["model_path"])

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Brain Tumor MRI Classifier API", version="1.0")

# CORS: open for file:// and localhost (development only — tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Pipeline — loaded once at startup, reused for every request ───────────────
_pipeline = None


@app.on_event("startup")
async def load_pipeline() -> None:
    global _pipeline
    from src.inference.predict import InferencePipeline
    ood_path = OOD_MODEL_PATH if OOD_MODEL_PATH.exists() else None
    _pipeline = InferencePipeline(
        classifier_path=CLASSIFIER_PATH,
        ood_model_path=ood_path,
        device="cpu",
    )
    logger.info("Pipeline ready | classifier=%s | ood=%s", CLASSIFIER_PATH, ood_path)


# ── Response schema ───────────────────────────────────────────────────────────
class PredictResponse(BaseModel):
    state: str                        # HIGH_CONFIDENCE_TUMOR | HIGH_CONFIDENCE_CLEAR | UNCERTAIN | OOD_REJECTED | ERROR
    label: str
    confidence: float | None          # Only set for HIGH_CONFIDENCE states
    tumor_probability: float | None
    no_tumor_probability: float | None
    original_image: str | None        # Base64-encoded PNG of the original MRI
    gradcam_image: str | None         # Base64-encoded PNG of the Grad-CAM overlay (high-confidence only)
    latency_ms: float
    error_message: str | None


# ── Helper: PIL Image → base64 PNG string ─────────────────────────────────────
def _pil_to_b64(img: Image.Image | None) -> str | None:
    if img is None:
        return None
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health() -> dict:
    """Quick liveness check used by the HTML frontend to show connection status."""
    return {"status": "ok", "model_loaded": _pipeline is not None}


@app.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)) -> PredictResponse:
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet — retry in a moment.")

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail=f"Expected an image file, got: {file.content_type}")

    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")

    try:
        pil_image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}")

    result = _pipeline.run(pil_image)

    return PredictResponse(
        state=result.state,
        label=result.label,
        confidence=result.confidence,
        tumor_probability=result.tumor_probability,
        no_tumor_probability=result.no_tumor_probability,
        original_image=_pil_to_b64(result.original_image),
        gradcam_image=_pil_to_b64(result.gradcam_overlay),
        latency_ms=result.latency_ms,
        error_message=result.error_message,
    )
