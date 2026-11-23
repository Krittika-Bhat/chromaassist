"""
daltonize.py
============
Daltonization: a technique to shift colour information from channels that a
colour-vision-deficient (CVD) person cannot perceive into channels they can.

Algorithm (Fidaner, Çoltekin & Ünsalan 2005 – widely known as "daltonize")
---------------------------------------------------------------------------
1. Simulate how the CVD observer would see the original image → S
2. Compute the error signal:  E = original - simulated   (signed, int16)
3. Multiply the error by a correction matrix M:  shift = M × E
4. Add the shift back to the original:  corrected = original + shift
5. Clip to [0, 255].

The matrix M routes information from the confused channels into the channels
that the observer CAN perceive.  For protan/deuteranopia the red and green
channels are confused, so their error is redistributed into the blue channel
(and to a lesser extent into brightness).  For tritanopia the blue channel
error is redistributed into red and green.

The default matrix M below is a commonly used constant; it is exposed as a
module-level variable so callers can override it without changing the code.

Two correction modes
--------------------
- "global"   – apply the correction to every pixel
- "targeted" – apply the correction only inside the confusion mask built by
               segmentation.build_confusion_mask(); pixels outside the mask
               are returned unchanged
"""

import numpy as np
from .simulation import simulate
from .segmentation import build_confusion_mask, mask_stats


# ---------------------------------------------------------------------------
# Daltonization matrices
# Rows = output channel (R, G, B)  |  Columns = error channel (R, G, B)
#
# For Protanopia / Deuteranopia:
# We adopt the Fidaner, Çoltekin & Ünsalan (2005) protocol:
#   Row 0 (R): [0.0, 0.0, 0.0] - keep original R signal
#   Row 1 (G): [0.7, 1.0, 0.0] - shift red and green error into green
#   Row 2 (B): [0.7, 0.0, 1.0] - shift red and blue error into blue
# This redistributes lost red-green chromatic contrast into both brightness
# and the blue channel, substantially improving pair discriminability.
# ---------------------------------------------------------------------------
DEFAULT_DALTONIZE_MATRICES = {
    "protanopia": np.array([
        [0.0, 0.0, 0.0],
        [0.7, 1.0, 0.0],
        [0.7, 0.0, 1.0],
    ], dtype=np.float64),
    "deuteranopia": np.array([
        [0.0, 0.0, 0.0],
        [0.7, 1.0, 0.0],
        [0.7, 0.0, 1.0],
    ], dtype=np.float64),
    "tritanopia": np.array([
        [1.0, 0.0, 0.7],
        [0.0, 1.0, 0.7],
        [0.0, 0.0, 0.0],
    ], dtype=np.float64),
}

# Exposed default constant for backwards compatibility
DEFAULT_DALTONIZE_MATRIX = DEFAULT_DALTONIZE_MATRICES["deuteranopia"]


def daltonize(
    img_uint8: np.ndarray,
    deficiency: str,
    severity: float = 1.0,
    method: str = "global",
    correction_matrix: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Apply daltonization to *img_uint8*.

    Parameters
    ----------
    img_uint8         : np.ndarray  (H, W, 3) uint8 sRGB
    deficiency        : str         'protanopia' | 'deuteranopia' | 'tritanopia'
    severity          : float       CVD severity passed to the simulator (0-1)
    method            : str         'global' or 'targeted'
    correction_matrix : np.ndarray  3×3 float64, overrides default matrix

    Returns
    -------
    corrected   : np.ndarray  (H, W, 3) uint8 – daltonized image
    simulated   : np.ndarray  (H, W, 3) uint8 – CVD-simulated original
    region_stats: dict        mask area and mean colour (empty dict for global)
    """
    if correction_matrix is not None:
        M = correction_matrix
    else:
        M = DEFAULT_DALTONIZE_MATRICES.get(deficiency, DEFAULT_DALTONIZE_MATRIX)

    # --- Step 1: Simulate CVD perception of the original ---
    simulated = simulate(img_uint8, deficiency, severity)

    # --- Step 2: Error map (signed arithmetic to avoid uint8 wrap-around) ---
    # E[pixel] = original[pixel] - simulated[pixel]
    # This captures the information that is "lost" through the simulation.
    error = img_uint8.astype(np.int16) - simulated.astype(np.int16)
    # shape: (H, W, 3), values in roughly [-255, 255]

    # --- Step 3: Compute the channel-shifted correction ---
    # Reshape to (N, 3), apply M, reshape back
    h, w = img_uint8.shape[:2]
    shift = (error.reshape(-1, 3).astype(np.float64) @ M.T).reshape(h, w, 3)

    # --- Step 4: Add shift to the original ---
    corrected_f = img_uint8.astype(np.float64) + shift

    # --- Step 5: Clip to valid uint8 range ---
    corrected = np.clip(corrected_f, 0.0, 255.0).round().astype(np.uint8)

    region_stats: dict = {}

    if method == "targeted":
        # Build a hue-based confusion mask and restrict the correction to
        # pixels inside that mask only.
        mask = build_confusion_mask(img_uint8, deficiency)  # (H, W) uint8 {0,255}
        region_stats = mask_stats(mask, img_uint8)

        # Blend: inside mask → corrected pixel; outside → original pixel
        mask_bool = mask > 0                               # (H, W) boolean
        # Expand mask to (H, W, 1) for broadcasting across 3 channels
        mask_3ch = mask_bool[..., np.newaxis]
        corrected = np.where(mask_3ch, corrected, img_uint8)

    elif method != "global":
        raise ValueError(f"Unknown method '{method}'. Use 'global' or 'targeted'.")

    return corrected, simulated, region_stats


def pseudocolor(img_uint8: np.ndarray, colormap: str = "viridis") -> np.ndarray:
    """
    Convert a colour image to a CVD-safe pseudo-colour representation.

    Steps:
      1. Convert RGB to luminance (greyscale) using the standard ITU-R BT.709
         coefficients: Y = 0.2126 R + 0.7152 G + 0.0722 B
      2. Map the greyscale intensity through a perceptually-uniform,
         CVD-safe matplotlib colormap (viridis or cividis).

    Both viridis and cividis are designed to be:
      • Perceptually uniform (equal steps in intensity = equal perceptual steps)
      • Readable by observers with protanopia or deuteranopia
      • Readable in greyscale (e.g. printed on a B&W laser printer)

    Parameters
    ----------
    img_uint8 : np.ndarray  (H, W, 3) uint8 sRGB
    colormap  : str         'viridis' (default) or 'cividis'

    Returns
    -------
    np.ndarray  (H, W, 3) uint8 – pseudo-coloured image
    """
    import matplotlib
    import matplotlib.cm as cm

    allowed = {"viridis", "cividis"}
    if colormap not in allowed:
        raise ValueError(f"Colormap must be one of {allowed}, got '{colormap}'.")

    # --- Step 1: Luminance (ITU-R BT.709) ---
    img_f = img_uint8.astype(np.float64) / 255.0
    # Weighted sum across the colour channels
    gray = (0.2126 * img_f[..., 0]
            + 0.7152 * img_f[..., 1]
            + 0.0722 * img_f[..., 2])  # shape (H, W), values in [0, 1]

    # --- Step 2: Apply colormap ---
    # matplotlib >= 3.9 removed cm.get_cmap(); use matplotlib.colormaps instead
    try:
        cmap = matplotlib.colormaps[colormap]   # preferred API (3.5+)
    except AttributeError:
        cmap = cm.get_cmap(colormap)            # fallback for older matplotlib
    # cmap() returns RGBA float values in [0, 1]; drop the alpha channel
    coloured = cmap(gray)[..., :3]    # shape (H, W, 3)

    return (coloured * 255.0).round().astype(np.uint8)
