"""
Out-of-Distribution (OOD) Detection Gate.

OOD means "Out-of-Distribution" — an image the model was never trained on and
cannot meaningfully classify. Without this gate, the main classifier will
confidently output "Tumor" or "No Tumor" even for a picture of a cat or a
chest X-ray, which would destroy clinical credibility.

This module provides TWO approaches so you can choose based on available time:
  - Approach A (preferred): MobileNetV2 binary classifier — "brain_mri" vs "other"
  - Approach B (fallback): Heuristic checks (image stats + edge density)
    Requires zero extra training. Less accurate but always works.

The active approach is selected via config.yaml (ood.approach).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import yaml
from PIL import Image
from torchvision import models, transforms
from torchvision.models import MobileNet_V2_Weights

_CONFIG_PATH = Path(__file__).parents[2] / "config.yaml"
with open(_CONFIG_PATH) as _f:
    _CFG = yaml.safe_load(_f)

_OOD_CFG = _CFG["ood"]
_IMG_SIZE: int = _OOD_CFG["image_size"]
_REJECTION_THRESHOLD: float = _OOD_CFG["rejection_threshold"]
_MEAN = _CFG["preprocessing"]["normalize_mean"]
_STD = _CFG["preprocessing"]["normalize_std"]

_OOD_TRANSFORM = transforms.Compose([
    transforms.Resize((_IMG_SIZE, _IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=_MEAN, std=_STD),
])


# -------------------------------------------------------------------
# Approach A: Lightweight MobileNetV2 OOD classifier
# -------------------------------------------------------------------

class OODGateModel(nn.Module):
    """
    MobileNetV2-based binary classifier: outputs P(is_brain_mri).
    MobileNetV2 has ~3.4M parameters — lighter than EfficientNetB0 and
    fast enough to add <200ms on CPU.
    Training this requires assembling a "not brain MRI" dataset (~500 images
    of chest X-rays, natural photos, etc.) — see notebooks/02_training.ipynb.
    """

    def __init__(self) -> None:
        super().__init__()
        self.backbone = models.mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
        in_features = self.backbone.classifier[1].in_features  # 1280
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_features, 1),  # single output: P(is_brain_mri)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.backbone(x))


def load_ood_model(weights_path: str | Path, device: str = "cpu") -> OODGateModel:
    """Load a trained OOD gate model from a checkpoint file."""
    weights_path = Path(weights_path)
    if not weights_path.exists():
        raise FileNotFoundError(
            f"OOD gate weights not found at: {weights_path}\n"
            "Train the OOD gate in notebooks/02_training.ipynb or use heuristic fallback."
        )
    model = OODGateModel()
    state = torch.load(weights_path, map_location=device, weights_only=True)
    if "model_state_dict" in state:
        model.load_state_dict(state["model_state_dict"])
    else:
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def is_brain_mri_model(
    pil_image: Image.Image,
    model: OODGateModel,
    device: str = "cpu",
) -> tuple[bool, float]:
    """
    Run the MobileNetV2 OOD gate.
    Returns:
        (is_valid, confidence) — True if the image is likely a brain MRI.
    """
    tensor = _OOD_TRANSFORM(pil_image).unsqueeze(0).to(device)
    prob = model(tensor).item()
    return prob >= _REJECTION_THRESHOLD, prob


# -------------------------------------------------------------------
# Approach B: Heuristic OOD check (no model training required)
# -------------------------------------------------------------------

def is_brain_mri_heuristic(pil_image: Image.Image) -> tuple[bool, float]:
    """
    Estimate whether an image is a brain MRI using statistical heuristics.
    This works because brain MRI images share a distinctive visual profile:
      - Predominantly dark background (high proportion of near-black pixels)
      - Circular/oval bright region (the brain) surrounded by black
      - High edge density in a roughly central region
      - Grayscale or near-grayscale color distribution (not colorful photos)

    Returns:
        (is_valid, confidence_score) — confidence is a heuristic score in [0, 1].
    """
    import cv2

    img_rgb = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # Signal 1: dark background dominance
    # Brain MRIs have large black borders; natural photos rarely do.
    dark_pixel_ratio = np.mean(gray < 30)

    # Signal 2: color saturation check
    # MRI images are grayscale. If the image has strong color saturation it is NOT an MRI.
    img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    mean_saturation = np.mean(img_hsv[:, :, 1]) / 255.0
    is_grayscale_like = mean_saturation < 0.15

    # Signal 3: edge density in center region
    # Brain MRIs have concentrated edges in the center where the skull/brain tissue is.
    h, w = gray.shape
    center_crop = gray[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    edges = cv2.Canny(center_crop, 50, 150)
    edge_density = np.mean(edges > 0)

    # Combine signals into a simple score
    score = 0.0
    if dark_pixel_ratio > 0.25:
        score += 0.35
    if is_grayscale_like:
        score += 0.40
    if 0.05 < edge_density < 0.35:
        score += 0.25

    is_valid = score >= _REJECTION_THRESHOLD
    return is_valid, score


# -------------------------------------------------------------------
# Unified public interface — used by the inference pipeline
# -------------------------------------------------------------------

def check_is_brain_mri(
    pil_image: Image.Image,
    ood_model: OODGateModel | None = None,
    device: str = "cpu",
) -> tuple[bool, float]:
    """
    Single entry point for the OOD gate.
    Uses the trained model if provided, falls back to heuristic if not.

    Args:
        pil_image: The uploaded image as a PIL RGB image.
        ood_model: Trained OODGateModel instance, or None to use heuristic.
        device: 'cpu' or 'cuda'.

    Returns:
        (is_valid, confidence) — is_valid=False triggers upload rejection.
    """
    if ood_model is not None:
        return is_brain_mri_model(pil_image, ood_model, device)
    return is_brain_mri_heuristic(pil_image)
