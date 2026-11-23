"""
test_simulation.py
==================
Unit tests for the CVD simulation module.

Tested properties
-----------------
1. Identity at severity=0  – the simulated image must equal the input exactly
2. Output range            – all pixel values stay in [0, 255]
3. Effect at severity=1    – the output must differ from the input (mean diff > 1)
"""

import numpy as np
import pytest
import sys, os

# Make sure the backend package root is on the path when running from /tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from processing.simulation import simulate

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

DEFICIENCIES = ["protanopia", "deuteranopia", "tritanopia"]


def make_random_image(seed: int = 42, h: int = 64, w: int = 64) -> np.ndarray:
    """Generate a reproducible random uint8 RGB image."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)


def make_colorful_image(h: int = 64, w: int = 64) -> np.ndarray:
    """
    Generate a synthetic image with vivid reds and greens side by side so
    that the CVD simulation matrices have something meaningful to change.
    """
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, : w // 2] = [220, 30, 30]   # vivid red on the left half
    img[:, w // 2 :] = [30, 200, 30]   # vivid green on the right half
    return img


# ---------------------------------------------------------------------------
# 1. Identity at severity=0
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deficiency", DEFICIENCIES)
def test_identity_at_severity_zero(deficiency):
    """
    At severity=0 the effective matrix is the identity, so the output must
    be pixel-identical to the input (after the round-trip through linear
    space and back, which at severity=0 is a no-op).
    """
    img = make_random_image()
    result = simulate(img, deficiency, severity=0.0)
    assert result.dtype == np.uint8
    assert result.shape == img.shape
    # Allow ±1 rounding tolerance from float → uint8 round-trip
    assert np.max(np.abs(result.astype(np.int16) - img.astype(np.int16))) <= 1, (
        f"[{deficiency}] severity=0 output differs from input by more than ±1 LSB"
    )


# ---------------------------------------------------------------------------
# 2. Output values stay within [0, 255]
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deficiency", DEFICIENCIES)
@pytest.mark.parametrize("severity", [0.0, 0.5, 1.0])
def test_output_range(deficiency, severity):
    """All pixel values in the simulated image must be valid uint8 (0-255)."""
    img = make_random_image()
    result = simulate(img, deficiency, severity)
    assert result.min() >= 0
    assert result.max() <= 255
    assert result.dtype == np.uint8


# ---------------------------------------------------------------------------
# 3. Simulation differs from the original at severity=1
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deficiency", DEFICIENCIES)
def test_differs_at_severity_one(deficiency):
    """
    At severity=1 the simulated image must look different from the original
    (mean absolute pixel difference should be non-trivial for a vivid image).
    """
    img = make_colorful_image()
    result = simulate(img, deficiency, severity=1.0)
    mean_diff = np.abs(result.astype(np.int16) - img.astype(np.int16)).mean()
    assert mean_diff > 1.0, (
        f"[{deficiency}] severity=1 simulation barely changed the image "
        f"(mean diff={mean_diff:.4f}); check the Machado matrices."
    )


# ---------------------------------------------------------------------------
# 4. Invalid deficiency name raises ValueError
# ---------------------------------------------------------------------------

def test_invalid_deficiency_raises():
    img = make_random_image()
    with pytest.raises(ValueError, match="Unknown deficiency"):
        simulate(img, "unknownopia", severity=1.0)
