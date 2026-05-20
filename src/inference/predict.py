"""
Full inference pipeline with the dual-confidence threshold engine.

This module is the single entry point for classification at runtime.
It chains together: OOD gate → classifier → threshold engine → Grad-CAM.

Threshold states (from PRD §7, Story C3):
  HIGH_CONFIDENCE_TUMOR  — P(tumor) >= 0.90 → red card
  HIGH_CONFIDENCE_CLEAR  — P(no_tumor) >= 0.90 → green card
  UNCERTAIN              — neither class reaches 0.90 → amber card
  OOD_REJECTED           — OOD gate failed → upload rejection
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import torch.nn.functional as F
import yaml
from PIL import Image

from src.data.preprocessing import image_to_hash, preprocess_image
from src.explainability.gradcam import generate_gradcam, overlay_heatmap
from src.model.classifier import BrainTumorClassifier, load_model
from src.model.ood_gate import OODGateModel, check_is_brain_mri

_CONFIG_PATH = Path(__file__).parents[2] / "config.yaml"
with open(_CONFIG_PATH) as _f:
    _CFG = yaml.safe_load(_f)

_HIGH_CONF_THRESHOLD: float = _CFG["inference"]["high_confidence_threshold"]
_CLASS_NAMES: list[str] = _CFG["dataset"]["class_names"]  # ["no_tumor", "tumor"]

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Result dataclass — structured output of the full pipeline
# -------------------------------------------------------------------

@dataclass
class PredictionResult:
    """
    All information the Streamlit app needs to render a result card.
    Using a dataclass instead of a plain dict prevents typos and makes
    the result self-documenting.
    """
    state: str                          # HIGH_CONFIDENCE_TUMOR | HIGH_CONFIDENCE_CLEAR | UNCERTAIN | OOD_REJECTED | ERROR
    label: str                          # Human-readable label shown on the card
    confidence: Optional[float] = None  # Only set for HIGH_CONFIDENCE states
    tumor_probability: Optional[float] = None
    no_tumor_probability: Optional[float] = None
    show_gradcam: bool = False
    gradcam_overlay: Optional[object] = None  # PIL Image or numpy array
    original_image: Optional[Image.Image] = None
    latency_ms: float = 0.0
    error_message: Optional[str] = None


# -------------------------------------------------------------------
# Threshold engine (pure function — no side effects, easy to unit test)
# -------------------------------------------------------------------

def apply_threshold(
    tumor_prob: float,
    no_tumor_prob: float,
    threshold: float = _HIGH_CONF_THRESHOLD,
) -> dict:
    """
    Core decision logic for the dual-confidence threshold engine.

    The dual threshold means BOTH a confident "Tumor" AND a confident
    "No Tumor" are treated as decisive results. Anything below threshold
    goes to the amber "Manual Review" state.

    Args:
        tumor_prob: P(tumor) output from the classifier softmax.
        no_tumor_prob: P(no_tumor) output.
        threshold: Minimum confidence required for a decisive result (default 0.90).

    Returns:
        Dict with state, label, confidence, and show_gradcam flag.
    """
    if tumor_prob >= threshold:
        return {
            "state": "HIGH_CONFIDENCE_TUMOR",
            "label": "Tumor Detected",
            "confidence": tumor_prob,
            "show_gradcam": True,
        }
    if no_tumor_prob >= threshold:
        return {
            "state": "HIGH_CONFIDENCE_CLEAR",
            "label": "No Tumor Detected",
            "confidence": no_tumor_prob,
            "show_gradcam": True,
        }
    return {
        "state": "UNCERTAIN",
        "label": "Manual Review Required",
        "confidence": None,
        "show_gradcam": False,
    }


# -------------------------------------------------------------------
# Full inference pipeline
# -------------------------------------------------------------------

class InferencePipeline:
    """
    Orchestrates the full inference flow:
      1. Preprocess image
      2. OOD gate
      3. Classify
      4. Apply threshold
      5. Generate Grad-CAM (only for high-confidence results)
      6. Log event

    Designed to be instantiated once (model loaded once) and called
    multiple times — avoids reloading weights on each request.
    """

    def __init__(
        self,
        classifier_path: str | Path,
        ood_model_path: Optional[str | Path] = None,
        device: str = "cpu",
    ) -> None:
        self.device = device

        self.classifier: BrainTumorClassifier = load_model(classifier_path, device)
        self.classifier.eval()

        self.ood_model: Optional[OODGateModel] = None
        if ood_model_path and Path(ood_model_path).exists():
            from src.model.ood_gate import load_ood_model
            self.ood_model = load_ood_model(ood_model_path, device)

        logger.info("InferencePipeline ready | device=%s | ood_model=%s", device, ood_model_path)

    def run(self, image_input) -> PredictionResult:
        """
        Run the full pipeline on a single image.

        Args:
            image_input: File path, numpy array, or PIL Image.

        Returns:
            PredictionResult with all fields populated.
        """
        start = time.perf_counter()
        image_hash = "unknown"

        try:
            # Step 1 — Preprocess
            tensor, pil_image = preprocess_image(image_input)
            image_hash = image_to_hash(image_input)

            # Step 2 — OOD gate
            is_valid, ood_confidence = check_is_brain_mri(pil_image, self.ood_model, self.device)
            _log_event("ood_gate_executed", {
                "result": "pass" if is_valid else "reject",
                "image_hash": image_hash,
            })

            if not is_valid:
                _log_event("ood_rejection_triggered", {"image_hash": image_hash})
                return PredictionResult(
                    state="OOD_REJECTED",
                    label="Not a Brain MRI",
                    error_message="This does not appear to be a brain MRI scan. Please upload a 2D brain MRI slice in JPG or PNG format.",
                    latency_ms=_elapsed_ms(start),
                    original_image=pil_image,
                )

            # Step 3 — Classify
            tensor = tensor.to(self.device)
            with torch.no_grad():
                logits = self.classifier(tensor)
                probs = F.softmax(logits, dim=1).squeeze()

            no_tumor_prob = probs[0].item()
            tumor_prob = probs[1].item()

            # Step 4 — Threshold engine
            threshold_result = apply_threshold(tumor_prob, no_tumor_prob)
            state = threshold_result["state"]

            _log_event("inference_executed", {
                "predicted_class": "tumor" if tumor_prob > no_tumor_prob else "no_tumor",
                "confidence_score": round(max(tumor_prob, no_tumor_prob), 4),
                "threshold_state": state,
                "image_hash": image_hash,
            })

            if state == "UNCERTAIN":
                _log_event("fallback_triggered", {
                    "tumor_probability": round(tumor_prob, 4),
                    "no_tumor_probability": round(no_tumor_prob, 4),
                    "image_hash": image_hash,
                })

            # Step 5 — Grad-CAM (only for high-confidence results)
            gradcam_overlay = None
            if threshold_result["show_gradcam"]:
                target_class = 1 if state == "HIGH_CONFIDENCE_TUMOR" else 0
                try:
                    heatmap = generate_gradcam(self.classifier, tensor, target_class)
                    gradcam_overlay = overlay_heatmap(pil_image, heatmap)
                    _log_event("gradcam_generated", {"target_class": target_class, "image_hash": image_hash})
                except Exception as exc:
                    logger.warning("Grad-CAM failed (non-fatal): %s", exc)

            latency = _elapsed_ms(start)

            return PredictionResult(
                state=state,
                label=threshold_result["label"],
                confidence=threshold_result["confidence"],
                tumor_probability=tumor_prob,
                no_tumor_probability=no_tumor_prob,
                show_gradcam=threshold_result["show_gradcam"],
                gradcam_overlay=gradcam_overlay,
                original_image=pil_image,
                latency_ms=latency,
            )

        except ValueError as exc:
            # Raised by preprocessing for bad images (too small, corrupt, etc.)
            _log_event("pipeline_error", {"error_type": "ValueError", "stage": "preprocessing", "message": str(exc)})
            return PredictionResult(
                state="ERROR",
                label="Invalid Image",
                error_message=str(exc),
                latency_ms=_elapsed_ms(start),
            )
        except Exception as exc:
            _log_event("pipeline_error", {"error_type": type(exc).__name__, "stage": "unknown", "message": str(exc)})
            logger.exception("Unexpected error in inference pipeline")
            return PredictionResult(
                state="ERROR",
                label="Processing Error",
                error_message="An unexpected error occurred. Please try again.",
                latency_ms=_elapsed_ms(start),
            )


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)


def _log_event(event: str, properties: dict) -> None:
    """Write a structured log line. No PII (no file paths, no patient data)."""
    import json
    import time as _time
    record = {"timestamp": _time.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "properties": properties}
    logger.info(json.dumps(record))
