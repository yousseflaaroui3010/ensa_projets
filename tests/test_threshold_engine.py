"""
Unit tests for the dual-confidence threshold engine (src/inference/predict.py).

Tests verify all three confidence states defined in PRD §7 Story C3:
  - HIGH_CONFIDENCE_TUMOR  (P(tumor) >= 0.90)
  - HIGH_CONFIDENCE_CLEAR  (P(no_tumor) >= 0.90)
  - UNCERTAIN              (neither class reaches 0.90)

These tests do NOT require a trained model — they test pure logic only.
Run with: python -m pytest tests/ -v
"""

import pytest
from src.inference.predict import apply_threshold


# ─────────────────────────────────────────────────────────────────────────────
# Happy path: high-confidence tumor
# ─────────────────────────────────────────────────────────────────────────────

class TestHighConfidenceTumor:
    def test_exactly_at_threshold(self):
        result = apply_threshold(tumor_prob=0.90, no_tumor_prob=0.10)
        assert result["state"] == "HIGH_CONFIDENCE_TUMOR"

    def test_above_threshold(self):
        result = apply_threshold(tumor_prob=0.97, no_tumor_prob=0.03)
        assert result["state"] == "HIGH_CONFIDENCE_TUMOR"
        assert result["label"] == "Tumor Detected"

    def test_confidence_value_is_tumor_prob(self):
        result = apply_threshold(tumor_prob=0.96, no_tumor_prob=0.04)
        assert result["confidence"] == pytest.approx(0.96)

    def test_gradcam_shown_for_tumor(self):
        result = apply_threshold(tumor_prob=0.95, no_tumor_prob=0.05)
        assert result["show_gradcam"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Happy path: high-confidence no tumor
# ─────────────────────────────────────────────────────────────────────────────

class TestHighConfidenceClear:
    def test_exactly_at_threshold(self):
        result = apply_threshold(tumor_prob=0.10, no_tumor_prob=0.90)
        assert result["state"] == "HIGH_CONFIDENCE_CLEAR"

    def test_above_threshold(self):
        result = apply_threshold(tumor_prob=0.04, no_tumor_prob=0.96)
        assert result["state"] == "HIGH_CONFIDENCE_CLEAR"
        assert result["label"] == "No Tumor Detected"

    def test_confidence_value_is_no_tumor_prob(self):
        result = apply_threshold(tumor_prob=0.05, no_tumor_prob=0.95)
        assert result["confidence"] == pytest.approx(0.95)

    def test_gradcam_shown_for_clear(self):
        result = apply_threshold(tumor_prob=0.05, no_tumor_prob=0.95)
        assert result["show_gradcam"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Uncertain: neither class reaches threshold → manual review
# ─────────────────────────────────────────────────────────────────────────────

class TestUncertain:
    def test_both_below_threshold(self):
        result = apply_threshold(tumor_prob=0.67, no_tumor_prob=0.33)
        assert result["state"] == "UNCERTAIN"

    def test_label_is_manual_review(self):
        result = apply_threshold(tumor_prob=0.55, no_tumor_prob=0.45)
        assert result["label"] == "Manual Review Required"

    def test_confidence_is_none(self):
        result = apply_threshold(tumor_prob=0.60, no_tumor_prob=0.40)
        assert result["confidence"] is None

    def test_gradcam_not_shown(self):
        result = apply_threshold(tumor_prob=0.60, no_tumor_prob=0.40)
        assert result["show_gradcam"] is False

    def test_just_below_threshold(self):
        # 0.899 should NOT trigger high confidence
        result = apply_threshold(tumor_prob=0.899, no_tumor_prob=0.101)
        assert result["state"] == "UNCERTAIN"


# ─────────────────────────────────────────────────────────────────────────────
# Boundary / edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestBoundaryCases:
    def test_custom_threshold_lower(self):
        # If we lower the threshold to 0.80, 0.85 should become decisive
        result = apply_threshold(tumor_prob=0.85, no_tumor_prob=0.15, threshold=0.80)
        assert result["state"] == "HIGH_CONFIDENCE_TUMOR"

    def test_custom_threshold_higher(self):
        # If we raise the threshold to 0.95, 0.92 should remain uncertain
        result = apply_threshold(tumor_prob=0.92, no_tumor_prob=0.08, threshold=0.95)
        assert result["state"] == "UNCERTAIN"

    def test_equal_probabilities(self):
        # 0.50 / 0.50 — model has no idea — must be uncertain
        result = apply_threshold(tumor_prob=0.50, no_tumor_prob=0.50)
        assert result["state"] == "UNCERTAIN"

    def test_tumor_takes_priority_when_both_would_hit(self):
        # Theoretically impossible from softmax, but the logic should still be
        # deterministic: tumor check runs first.
        result = apply_threshold(tumor_prob=0.91, no_tumor_prob=0.91, threshold=0.90)
        assert result["state"] == "HIGH_CONFIDENCE_TUMOR"
