"""
simulation.py
=============
Colour-vision-deficiency (CVD) simulation using the method of
Machado, Oliveira & Fernandes (2009).

Reference
---------
Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009).
"A Physiologically-based Model for Simulation of Color Vision Deficiency."
IEEE Transactions on Visualization and Computer Graphics, 15(6), 1291-1298.

How it works
------------
1. Convert the input sRGB image to **linear RGB** (removes gamma).
2. Multiply every pixel (as a 3-vector) by a 3×3 Machado matrix.
   The matrix "collapses" the missing cone's information onto the
   remaining two cones, simulating what a dichromat would perceive.
3. Convert the result back to sRGB (re-applies gamma).

Severity interpolation
----------------------
At severity=0 we use the identity matrix I  → output equals input.
At severity=1 we use the full Machado matrix M.
In between:   M_eff = (1 - severity) * I  +  severity * M
This is a simple linear (affine) interpolation in matrix space.
"""

import numpy as np
from .color_spaces import srgb_to_linear, linear_to_srgb


# ---------------------------------------------------------------------------
# Machado et al. 2009 – full-severity simulation matrices (linear RGB space)
# Rows = output R, G, B  |  Columns = input R, G, B
# ---------------------------------------------------------------------------

MACHADO_MATRICES = {
    # Protanopia – missing L (long-wavelength / "red") cones
    "protanopia": np.array([
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281,  0.099216],
        [-0.003882, -0.048116,  1.051998],
    ]),
    # Deuteranopia – missing M (medium-wavelength / "green") cones
    "deuteranopia": np.array([
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501,  0.047413],
        [-0.011820,  0.042940,  0.968881],
    ]),
    # Tritanopia – missing S (short-wavelength / "blue") cones
    "tritanopia": np.array([
        [1.255528, -0.076749, -0.178779],
        [-0.078411,  0.930809,  0.147602],
        [0.004733,  0.691367,  0.303900],
    ]),
}

# 3×3 identity matrix used for the severity-0 endpoint
_IDENTITY = np.eye(3, dtype=np.float64)


def _get_effective_matrix(deficiency: str, severity: float) -> np.ndarray:
    """
    Return the interpolated simulation matrix for the requested deficiency
    and severity level.

    M_eff = (1 - severity) * I  +  severity * M_full

    At severity=0  → M_eff == I  (no change to the image)
    At severity=1  → M_eff == M_full (maximum simulation)
    """
    if deficiency not in MACHADO_MATRICES:
        raise ValueError(
            f"Unknown deficiency '{deficiency}'. "
            f"Choose from: {list(MACHADO_MATRICES.keys())}"
        )
    severity = float(np.clip(severity, 0.0, 1.0))
    M_full = MACHADO_MATRICES[deficiency]
    # Affine blend between identity and full matrix
    M_eff = (1.0 - severity) * _IDENTITY + severity * M_full
    return M_eff


def simulate(
    img_uint8: np.ndarray,
    deficiency: str,
    severity: float = 1.0,
) -> np.ndarray:
    """
    Simulate how a colour-vision-deficient observer perceives *img_uint8*.

    Parameters
    ----------
    img_uint8  : np.ndarray  shape (H, W, 3), dtype uint8, sRGB values 0-255
    deficiency : str         one of 'protanopia', 'deuteranopia', 'tritanopia'
    severity   : float       0 (no effect) to 1 (full simulation)

    Returns
    -------
    np.ndarray  shape (H, W, 3), dtype uint8, simulated image in sRGB 0-255
    """
    # --- Step 1: sRGB uint8 → linear float64 [0, 1] ---
    img_f = img_uint8.astype(np.float64) / 255.0
    lin = srgb_to_linear(img_f)

    # --- Step 2: Apply the (interpolated) simulation matrix ---
    M = _get_effective_matrix(deficiency, severity)
    h, w = lin.shape[:2]
    # Reshape to (N, 3), matrix-multiply, reshape back
    sim_lin = (lin.reshape(-1, 3) @ M.T).reshape(h, w, 3)

    # --- Step 3: Clip to [0, 1] then back to sRGB uint8 ---
    sim_srgb = linear_to_srgb(np.clip(sim_lin, 0.0, 1.0))
    return (sim_srgb * 255.0).round().astype(np.uint8)
