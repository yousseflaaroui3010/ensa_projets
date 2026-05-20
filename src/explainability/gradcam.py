"""
Grad-CAM (Gradient-weighted Class Activation Mapping) explainability module.

What Grad-CAM does in plain English:
  It asks the model: "Which pixels in this image most strongly influenced
  your prediction?" Then it draws a heat map — red = high influence,
  blue = low influence — overlaid on the original MRI scan.

  This is critical for doctor trust: if the model says "Tumor Detected" and
  the heatmap highlights the right region of the brain, the doctor has a
  visual reason to trust the prediction. If the heatmap highlights the
  background or the skull edge, the doctor knows to be skeptical.

Why the last convolutional layer:
  The last conv layer (features[-1] in EfficientNetB0) encodes the highest-level
  semantic features — shapes, textures — that the model actually "looks at"
  when deciding the class. Earlier layers encode low-level details (edges, colors)
  that are less meaningful for interpretation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import yaml
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

_CONFIG_PATH = Path(__file__).parents[2] / "config.yaml"
with open(_CONFIG_PATH) as _f:
    _CFG = yaml.safe_load(_f)

_ALPHA: float = _CFG["gradcam"]["heatmap_alpha"]


def generate_gradcam(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    target_class: int,
) -> np.ndarray:
    """
    Generate a Grad-CAM heatmap for a single image.

    Args:
        model: The trained BrainTumorClassifier (must be in eval mode).
        input_tensor: Shape (1, 3, 224, 224) — the preprocessed image tensor.
        target_class: The class index to explain (0=no_tumor, 1=tumor).

    Returns:
        heatmap: Numpy array of shape (224, 224), values in [0, 1].
                 0 = low model attention, 1 = high model attention.
    """
    # The target layer is the last convolutional block of EfficientNetB0.
    # For torchvision's EfficientNetB0, this is model.backbone.features[-1].
    target_layers = [model.backbone.features[-1]]

    cam = GradCAM(model=model, target_layers=target_layers)

    # GradCAM targets: None means "explain the predicted class".
    # We pass the actual target_class to ensure we explain the right output
    # even when the model is uncertain.
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    targets = [ClassifierOutputTarget(target_class)]

    heatmap = cam(input_tensor=input_tensor, targets=targets)
    return heatmap[0]  # shape: (224, 224), values in [0, 1]


def overlay_heatmap(
    original_image: Image.Image,
    heatmap: np.ndarray,
    alpha: float = _ALPHA,
) -> Image.Image:
    """
    Blend the Grad-CAM heatmap with the original MRI image for display.

    The original image is shown clearly with the colored heatmap on top
    at the configured transparency level (alpha).

    Args:
        original_image: PIL RGB image (the uploaded MRI, before any preprocessing).
        heatmap: Grad-CAM output array (H, W) with values in [0, 1].
        alpha: Transparency of the heatmap layer (0=invisible, 1=fully opaque).

    Returns:
        PIL Image with heatmap overlay, same size as original_image.
    """
    # Resize heatmap to match the original image dimensions
    orig_w, orig_h = original_image.size
    heatmap_resized = cv2.resize(heatmap, (orig_w, orig_h))

    # Convert original image to float32 numpy in [0, 1] range
    img_array = np.array(original_image.convert("RGB")).astype(np.float32) / 255.0

    # show_cam_on_image from pytorch-grad-cam blends using the jet colormap
    overlay = show_cam_on_image(img_array, heatmap_resized, use_rgb=True, image_weight=1 - alpha)

    return Image.fromarray(overlay)


def generate_and_overlay(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    original_image: Image.Image,
    target_class: int,
) -> tuple[np.ndarray, Image.Image]:
    """
    Convenience function: generate heatmap AND overlay in one call.
    Used by the Streamlit app.

    Returns:
        (raw_heatmap, overlay_image)
    """
    heatmap = generate_gradcam(model, input_tensor, target_class)
    overlay = overlay_heatmap(original_image, heatmap)
    return heatmap, overlay
