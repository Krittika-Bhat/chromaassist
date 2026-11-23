"""
test_daltonize.py
=================
Unit tests for the daltonize module.

Tested properties
-----------------
1. Output always clipped to [0, 255]
2. Global and targeted modes both return valid uint8 images
3. Targeted mode region_stats is populated
4. Pseudocolor output has correct shape and range
"""

import numpy as np
import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from processing.daltonize import daltonize, pseudocolor

DEFICIENCIES = ["protanopia", "deuteranopia", "tritanopia"]


def make_colorful_image(h: int = 64, w: int = 64) -> np.ndarray:
    """Vivid red/green image to exercise the correction matrices."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, : w // 2] = [220, 30, 30]
    img[:, w // 2 :] = [30, 200, 30]
    return img


# ---------------------------------------------------------------------------
# 1. Output range [0, 255]
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deficiency", DEFICIENCIES)
@pytest.mark.parametrize("method", ["global", "targeted"])
def test_daltonize_output_range(deficiency, method):
    """Corrected pixel values must stay within uint8 bounds."""
    img = make_colorful_image()
    corrected, simulated, _ = daltonize(img, deficiency, severity=1.0, method=method)
    assert corrected.dtype == np.uint8
    assert corrected.min() >= 0
    assert corrected.max() <= 255
    assert simulated.dtype == np.uint8
    assert simulated.min() >= 0
    assert simulated.max() <= 255


# ---------------------------------------------------------------------------
# 2. Shape preservation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deficiency", DEFICIENCIES)
def test_daltonize_shape(deficiency):
    """Output shape must match input shape."""
    img = make_colorful_image(h=50, w=80)
    corrected, simulated, _ = daltonize(img, deficiency, severity=1.0)
    assert corrected.shape == img.shape
    assert simulated.shape == img.shape


# ---------------------------------------------------------------------------
# 3. Targeted mode populates region_stats
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deficiency", ["protanopia", "deuteranopia"])
def test_targeted_region_stats(deficiency):
    """Targeted mode must return a non-empty region_stats dict."""
    img = make_colorful_image()
    _, _, region_stats = daltonize(img, deficiency, severity=1.0, method="targeted")
    assert isinstance(region_stats, dict)
    assert "area_pct" in region_stats
    assert "mean_color" in region_stats
    assert 0.0 <= region_stats["area_pct"] <= 100.0


# ---------------------------------------------------------------------------
# 4. Pseudocolor shape and range
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("colormap", ["viridis", "cividis"])
def test_pseudocolor(colormap):
    """Pseudocolor output must be uint8 with the same spatial dimensions."""
    img = make_colorful_image(h=32, w=48)
    out = pseudocolor(img, colormap)
    assert out.dtype == np.uint8
    assert out.shape == img.shape
    assert out.min() >= 0
    assert out.max() <= 255


# ---------------------------------------------------------------------------
# 5. Invalid method raises ValueError
# ---------------------------------------------------------------------------

def test_invalid_method_raises():
    img = make_colorful_image()
    with pytest.raises(ValueError, match="Unknown method"):
        daltonize(img, "deuteranopia", method="magic")


# ---------------------------------------------------------------------------
# 6. Pair discriminability metric
# ---------------------------------------------------------------------------

def test_pair_discriminability_metric():
    """Verify pair discriminability correctly detects red-green contrast recovery."""
    from processing.metrics import pair_discriminability

    img = np.zeros((40, 40, 3), dtype=np.uint8)
    img[:, :20] = [220, 30, 30]   # red
    img[:, 20:] = [30, 200, 30]   # green

    corrected, simulated, _ = daltonize(img, "deuteranopia", severity=1.0)
    from processing.simulation import simulate
    corrected_sim = simulate(corrected, "deuteranopia", severity=1.0)

    result = pair_discriminability(
        original=img,
        simulated_original=simulated,
        simulated_corrected=corrected_sim,
        deficiency="deuteranopia",
    )
    assert result["valid"] is True
    assert result["delta_e_simulated_original"] > 0
    assert result["delta_e_simulated_corrected"] > 0
    assert result["improvement_pct"] > 0

