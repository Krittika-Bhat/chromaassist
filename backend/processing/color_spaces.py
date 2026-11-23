"""
color_spaces.py
===============
Low-level colour-space conversion helpers.

All functions operate on float64 NumPy arrays whose pixel values are in the
range [0, 1] unless stated otherwise.  No external colour-science libraries
are used – every formula is implemented by hand so the maths can be explained
in a viva.
"""

import numpy as np


# ---------------------------------------------------------------------------
# sRGB  <->  linear RGB
# ---------------------------------------------------------------------------

def srgb_to_linear(img: np.ndarray) -> np.ndarray:
    """
    Remove sRGB gamma and return linear-light RGB values in [0, 1].

    sRGB uses a piecewise transfer function (IEC 61966-2-1):
        C_linear = C_srgb / 12.92                   if C_srgb <= 0.04045
        C_linear = ((C_srgb + 0.055) / 1.055) ^ 2.4  otherwise

    Working in linear RGB is mandatory before applying any linear colour
    transform (e.g. a CVD simulation matrix) so that channel mixing is
    physically correct.
    """
    img = img.astype(np.float64)
    # Boolean mask for the linear segment of the piecewise curve
    linear_mask = img <= 0.04045
    out = np.where(
        linear_mask,
        img / 12.92,                          # linear segment
        ((img + 0.055) / 1.055) ** 2.4        # gamma segment
    )
    return out


def linear_to_srgb(img: np.ndarray) -> np.ndarray:
    """
    Apply the sRGB gamma curve to linear-light RGB values in [0, 1].

    Inverse of srgb_to_linear:
        C_srgb = 12.92 * C_linear               if C_linear <= 0.0031308
        C_srgb = 1.055 * C_linear^(1/2.4) - 0.055  otherwise
    """
    img = np.clip(img, 0.0, 1.0)
    linear_mask = img <= 0.0031308
    out = np.where(
        linear_mask,
        12.92 * img,
        1.055 * np.power(img, 1.0 / 2.4) - 0.055
    )
    return np.clip(out, 0.0, 1.0)


# ---------------------------------------------------------------------------
# RGB  <->  HSV
# ---------------------------------------------------------------------------

def rgb_to_hsv(img: np.ndarray) -> np.ndarray:
    """
    Convert an RGB image (float64, [0,1]) to HSV.

    H in [0, 360), S in [0, 1], V in [0, 1].

    Algorithm (from Foley, van Dam et al.):
      V = max(R, G, B)
      S = (V - min) / V      (0 when V == 0)
      H is derived from which channel is the max and the relative
      distances between channels.
    """
    img = img.astype(np.float64)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]

    cmax = np.maximum(np.maximum(r, g), b)   # V
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin                       # chroma

    # --- Hue ---
    h = np.zeros_like(cmax)
    # Avoid division by zero
    nonzero = delta > 0
    # Max channel is R
    mask_r = nonzero & (cmax == r)
    h[mask_r] = 60.0 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
    # Max channel is G
    mask_g = nonzero & (cmax == g)
    h[mask_g] = 60.0 * ((b[mask_g] - r[mask_g]) / delta[mask_g] + 2)
    # Max channel is B
    mask_b = nonzero & (cmax == b)
    h[mask_b] = 60.0 * ((r[mask_b] - g[mask_b]) / delta[mask_b] + 4)

    # --- Saturation ---
    s = np.where(cmax > 0, delta / cmax, 0.0)

    # --- Value ---
    v = cmax

    return np.stack([h, s, v], axis=-1)


def hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    """
    Convert HSV (H in [0,360), S and V in [0,1]) back to RGB [0,1].

    Uses the standard sector-based formula with six 60-degree sectors.
    """
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    h = h % 360.0                    # wrap hue just in case
    hi = (h / 60.0).astype(int) % 6  # sector index 0-5
    f = h / 60.0 - np.floor(h / 60.0)

    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    r = np.select(
        [hi == 0, hi == 1, hi == 2, hi == 3, hi == 4, hi == 5],
        [v, q, p, p, t, v]
    )
    g = np.select(
        [hi == 0, hi == 1, hi == 2, hi == 3, hi == 4, hi == 5],
        [t, v, v, q, p, p]
    )
    b = np.select(
        [hi == 0, hi == 1, hi == 2, hi == 3, hi == 4, hi == 5],
        [p, p, t, v, v, q]
    )

    return np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)


# ---------------------------------------------------------------------------
# RGB  ->  CIELAB  (via XYZ)
# ---------------------------------------------------------------------------

# D65 illuminant XYZ reference white (standard for sRGB)
_D65_XYZ = np.array([0.95047, 1.00000, 1.08883])

# sRGB -> XYZ (D65) linear matrix (IEC 61966-2-1 Annex B)
_SRGB_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
])


def _f_lab(t: np.ndarray) -> np.ndarray:
    """
    CIE 1976 f() function used in the XYZ -> Lab conversion.
    f(t) = t^(1/3)         if t > (6/29)^3
    f(t) = t/(3*(6/29)^2) + 4/29  otherwise
    """
    delta = 6.0 / 29.0
    return np.where(
        t > delta ** 3,
        np.cbrt(t),
        t / (3 * delta ** 2) + 4.0 / 29.0
    )


def rgb_to_lab(img: np.ndarray) -> np.ndarray:
    """
    Convert sRGB uint8 image (H x W x 3) to CIELAB float64.

    Steps:
      1. Normalise to [0, 1]
      2. Remove sRGB gamma -> linear RGB
      3. Matrix-multiply by _SRGB_TO_XYZ -> CIE XYZ
      4. Normalise by D65 white point
      5. Apply f() -> L*, a*, b*
    """
    img_f = img.astype(np.float64) / 255.0
    lin = srgb_to_linear(img_f)                       # step 2

    # Reshape to (N, 3) for matrix multiply, then back
    h, w = lin.shape[:2]
    xyz = lin.reshape(-1, 3) @ _SRGB_TO_XYZ.T         # step 3
    xyz = xyz.reshape(h, w, 3)

    # Normalise by D65 white
    xyz_n = xyz / _D65_XYZ                             # step 4

    # Apply f()
    f = _f_lab(xyz_n)                                  # step 5

    L = 116.0 * f[..., 1] - 16.0
    a = 500.0 * (f[..., 0] - f[..., 1])
    b = 200.0 * (f[..., 1] - f[..., 2])

    return np.stack([L, a, b], axis=-1)
