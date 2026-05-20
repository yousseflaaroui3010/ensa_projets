"""
EfficientNetB0-based binary classifier for brain tumor detection.

Architecture:
  - Base: EfficientNetB0 pretrained on ImageNet (frozen in Phase 1, partially unfrozen in Phase 2)
  - Head: Dropout → Linear(1280 → 2) (two output classes: no_tumor, tumor)

EfficientNetB0 was chosen because it:
  - Has only ~5.3M parameters → fast CPU inference (<3s per image)
  - Was pre-trained on ImageNet (1.2M images) so its feature extraction is
    already strong; we only need to teach the final layer about brain tumors
  - Achieves 97–98% accuracy on this dataset according to published research
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn
import yaml
from torchvision import models
from torchvision.models import EfficientNet_B0_Weights

_CONFIG_PATH = Path(__file__).parents[2] / "config.yaml"
with open(_CONFIG_PATH) as _f:
    _CFG = yaml.safe_load(_f)

_MODEL_CFG = _CFG["model"]
_NUM_CLASSES: int = _MODEL_CFG["num_classes"]
_DROPOUT_RATE: float = _MODEL_CFG["dropout_rate"]


class BrainTumorClassifier(nn.Module):
    """
    Wraps EfficientNetB0 with a custom 2-class output head.
    The original EfficientNetB0 head was designed for 1,000 ImageNet categories —
    we replace it with a 2-class head for our binary task.
    """

    def __init__(self, num_classes: int = _NUM_CLASSES, dropout_rate: float = _DROPOUT_RATE) -> None:
        super().__init__()
        # Load pretrained EfficientNetB0 weights (downloaded from torchvision)
        self.backbone = models.efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)

        # Replace the original 1000-class head with our 2-class head
        in_features = self.backbone.classifier[1].in_features  # 1280 for B0
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout_rate, inplace=True),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def freeze_base(self) -> None:
        """
        Phase 1 training: freeze all layers except the classifier head.
        This makes training very fast because only the 2-class head
        (a few thousand parameters) needs to update.
        """
        for param in self.backbone.features.parameters():
            param.requires_grad = False
        for param in self.backbone.classifier.parameters():
            param.requires_grad = True

    def unfreeze_top_blocks(self, num_blocks: int = 2) -> None:
        """
        Phase 2 fine-tuning: unfreeze the last N convolutional blocks so the
        feature extractor can adapt to brain MRI texture — not just ImageNet objects.
        A low learning rate (1e-4) must be used to avoid overwriting the
        useful ImageNet weights with noise.
        """
        # EfficientNetB0 features[0..8] — unfreeze the last `num_blocks` sequential blocks
        feature_blocks = list(self.backbone.features.children())
        for block in feature_blocks[-num_blocks:]:
            for param in block.parameters():
                param.requires_grad = True

    def count_trainable_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# -------------------------------------------------------------------
# Convenience functions used by training notebooks and inference pipeline
# -------------------------------------------------------------------

def build_model(pretrained: bool = True) -> BrainTumorClassifier:
    """Create a fresh model instance with frozen base (Phase 1 ready)."""
    model = BrainTumorClassifier()
    model.freeze_base()
    return model


def load_model(weights_path: str | Path, device: torch.device | str = "cpu") -> BrainTumorClassifier:
    """
    Load a saved model from a .pt checkpoint file.
    Used by the inference pipeline and Streamlit app.

    Args:
        weights_path: Path to the .pt file saved during training.
        device: 'cpu' for laptop inference, 'cuda' for GPU.

    Returns:
        Model in eval mode, ready for inference.
    """
    weights_path = Path(weights_path)
    if not weights_path.exists():
        raise FileNotFoundError(
            f"Model weights not found at: {weights_path}\n"
            "Run notebooks/02_training.ipynb first to train and save the model."
        )
    model = BrainTumorClassifier()
    state = torch.load(weights_path, map_location=device, weights_only=True)
    # Support both raw state_dict saves and checkpoint dicts
    if "model_state_dict" in state:
        model.load_state_dict(state["model_state_dict"])
    else:
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


def get_class_weights(device: torch.device | str = "cpu") -> torch.Tensor:
    """
    Return the class weights tensor for the loss function.
    Tumor (class 1) is weighted higher to penalize missed tumors (False Negatives).
    Values come from config.yaml so they are easy to tune.
    """
    weights = _CFG["training"]["class_weights"]
    return torch.tensor(weights, dtype=torch.float32).to(device)
