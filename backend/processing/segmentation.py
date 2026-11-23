"""
segmentation.py
===============
HSV-based hue segmentation to build a mask of "confusing" colour regions
for targeted CVD correction.

Why targeted correction?
------------------------
Global daltonization shifts ALL colours in the image, which can introduce
unwanted artefacts in areas that were already distinguishable.  By computing
a mask that covers only the hue ranges that are genuinely confused by a
given deficiency, we limit the correction to those pixels only.

Hue ranges targeted
-------------------
Protan / Deutan deficiencies confuse:
  • Reds     – H  [0,  20] ∪ [340, 360)
  • Oranges  – H  [20, 45]
  • Greens   – H  [80, 160]
  • Browns   – H  [15, 40] with low S and V  (covered by orange range)

Tritan deficiency confuses:
  • Blues    – H  [200, 260]
  • Greens   – H  [80,  160]  (some overlap with blue-green)

The mask is then cleaned with morphological opening (removes tiny noise
spots) followed by closing (fills small holes) so the region boundaries
are smooth.
"""

import numpy as np
import cv2
from .color_spaces import rgb_to_hsv


# ---------------------------------------------------------------------------
# Hue ranges that cause confusion for each deficiency type
# Each entry is a list of (h_low, h_high) pairs in degrees [0, 360).
# ---------------------------------------------------------------------------
_CONFUSED_HUES: dict[str, list[tuple[float, float]]] = {
    "protanopia":   [(0, 20), (20, 45), (80, 160), (340, 360)],
    "deuteranopia": [(0, 20), (20, 45), (80, 160), (340, 360)],
    "tritanopia":   [(80, 160), (200, 260)],
}


def build_confusion_mask(
    img_uint8: np.ndarray,
    deficiency: str,
    min_saturation: float = 0.15,
    min_value: float = 0.10,
) -> np.ndarray:
    """
    Build a binary mask (uint8, 0 or 255) of pixels whose hue falls in one
    of the confusion ranges for the given deficiency.

    Parameters
    ----------
    img_uint8      : np.ndarray  (H, W, 3) uint8 sRGB
    deficiency     : str         'protanopia' | 'deuteranopia' | 'tritanopia'
    min_saturation : float       pixels with S < this are considered grey →
                                 not included in the mask (greys are not
                                 confused by dichromats in the same way)
    min_value      : float       very dark pixels (shadows) are skipped

    Returns
    -------
    mask : np.ndarray  (H, W) uint8, 255 inside confusion regions, 0 outside
    """
    if deficiency not in _CONFUSED_HUES:
        raise ValueError(
            f"Unknown deficiency '{deficiency}'. "
            f"Choose from: {list(_CONFUSED_HUES.keys())}"
        )

    # Convert to HSV float (H in [0,360), S and V in [0,1])
    img_f = img_uint8.astype(np.float64) / 255.0
    hsv = rgb_to_hsv(img_f)          # shape (H, W, 3)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    # Start with an all-zero mask
    mask = np.zeros(H.shape, dtype=bool)

    # Union of all confusion hue ranges
    for h_lo, h_hi in _CONFUSED_HUES[deficiency]:
        mask |= (H >= h_lo) & (H < h_hi)

    # Exclude achromatic (grey/dark) pixels
    mask &= (S >= min_saturation) & (V >= min_value)

    # Convert boolean -> uint8 {0, 255}
    mask_u8 = (mask.astype(np.uint8)) * 255

    # --- Morphological cleanup ---
    # Opening (erosion then dilation): removes isolated noise pixels
    # Closing (dilation then erosion): fills small holes in the mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN,  kernel)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)

    return mask_u8


def mask_stats(mask: np.ndarray, img_uint8: np.ndarray) -> dict:
    """
    Return simple statistics about the masked region:
      - area_pct  : percentage of image pixels inside the mask
      - mean_color: mean [R, G, B] (0-255) of pixels inside the mask,
                    or [0,0,0] when the mask is empty
    """
    total_pixels = mask.size
    inside = mask > 0
    area_pct = float(inside.sum()) / total_pixels * 100.0

    if inside.any():
        mean_color = img_uint8[inside].mean(axis=0).tolist()
    else:
        mean_color = [0.0, 0.0, 0.0]

    return {"area_pct": round(area_pct, 2), "mean_color": mean_color}
