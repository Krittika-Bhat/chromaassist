"""
metrics.py
==========
Image-quality metrics for the ChromaAssist pipeline.

Delta-E (ΔE) – the standard perceptual colour difference
---------------------------------------------------------
CIE 1976 ΔE₇₆ is the Euclidean distance in CIELAB colour space:

    ΔE = sqrt( (ΔL*)² + (Δa*)² + (Δb*)² )

Interpretation guide (approximate):
  ΔE < 1    : difference not perceptible to the human eye
  ΔE 1–2    : barely perceptible (trained observers only)
  ΔE 2–10   : perceptible at a glance
  ΔE 11–49  : colours are more similar than opposite
  ΔE > 100  : maximum (e.g. white vs black)

We compute the MEAN ΔE across all pixels, which gives a single scalar
summarising how much perceptual information is lost (original→simulated)
or recovered (corrected→its simulation).

Lower ΔE is BETTER:
  - original_vs_simulated   : low ΔE means little info lost through CVD
  - corrected_vs_simulated  : low ΔE means the correction helped the
                               CVD observer perceive the corrected image
                               similarly to how a normal observer sees the
                               original.
"""

import numpy as np
from .color_spaces import rgb_to_lab, rgb_to_hsv
from .simulation import simulate
from .segmentation import mask_stats


def delta_e_map(img_a: np.ndarray, img_b: np.ndarray) -> np.ndarray:
    """
    Compute per-pixel CIE 1976 ΔE between two uint8 sRGB images.

    Parameters
    ----------
    img_a, img_b : np.ndarray  (H, W, 3) uint8

    Returns
    -------
    np.ndarray  (H, W) float64 – per-pixel ΔE values
    """
    lab_a = rgb_to_lab(img_a)   # (H, W, 3)
    lab_b = rgb_to_lab(img_b)   # (H, W, 3)

    # Euclidean distance in Lab space (ΔE76)
    diff_sq = (lab_a - lab_b) ** 2           # squared differences per channel
    return np.sqrt(diff_sq.sum(axis=-1))     # (H, W)


def mean_delta_e(img_a: np.ndarray, img_b: np.ndarray) -> float:
    """
    Return the mean CIE 1976 ΔE across all pixels of two sRGB uint8 images.
    Lower = more similar / less information lost.
    """
    return float(delta_e_map(img_a, img_b).mean())


def pair_discriminability(
    original: np.ndarray,
    simulated_original: np.ndarray,
    simulated_corrected: np.ndarray,
    deficiency: str = "deuteranopia",
    min_pixels: int = 15,
) -> dict:
    """
    Compute the pair discriminability metric between two confusable color groups.

    For Protanopia / Deuteranopia:
      - Group 1: Red / Orange / Brown pixels
      - Group 2: Green / Olive pixels

    For Tritanopia:
      - Group 1: Blue / Violet pixels
      - Group 2: Green / Yellow pixels

    Steps:
      1. Segment both groups from the ORIGINAL image using HSV thresholds.
      2. Compute mean CIELAB color of Group 1 and Group 2 in `simulated_original`
         and calculate ΔE between the two means (baseline discriminability).
      3. Compute mean CIELAB color of Group 1 and Group 2 in `simulated_corrected`
         and calculate ΔE between the two means (post-correction discriminability).
      4. Compare: a higher post-correction ΔE indicates that the two confusable
         colors are now more distinguishable to a CVD observer.

    Returns
    -------
    dict with:
      - valid: bool
      - delta_e_simulated_original: float | None
      - delta_e_simulated_corrected: float | None
      - improvement_pct: float | None
      - group1_pixels: int
      - group2_pixels: int
    """
    img_f = original.astype(np.float64) / 255.0
    hsv = rgb_to_hsv(img_f)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    if deficiency in ("protanopia", "deuteranopia"):
        # Red / Orange / Brown
        mask_g1 = ((H >= 340.0) | (H < 45.0)) & (S >= 0.15) & (V >= 0.10)
        # Green / Olive
        mask_g2 = (H >= 65.0) & (H < 170.0) & (S >= 0.15) & (V >= 0.10)
        g1_name, g2_name = "Red/Orange/Brown", "Green"
    elif deficiency == "tritanopia":
        # Blue / Violet
        mask_g1 = (H >= 190.0) & (H < 270.0) & (S >= 0.15) & (V >= 0.10)
        # Green / Yellow
        mask_g2 = (H >= 60.0) & (H < 160.0) & (S >= 0.15) & (V >= 0.10)
        g1_name, g2_name = "Blue/Violet", "Green/Yellow"
    else:
        mask_g1 = np.zeros(H.shape, dtype=bool)
        mask_g2 = np.zeros(H.shape, dtype=bool)
        g1_name, g2_name = "Group 1", "Group 2"

    count_g1 = int(mask_g1.sum())
    count_g2 = int(mask_g2.sum())

    if count_g1 < min_pixels or count_g2 < min_pixels:
        return {
            "valid": False,
            "delta_e_simulated_original": None,
            "delta_e_simulated_corrected": None,
            "improvement_pct": None,
            "group1_name": g1_name,
            "group2_name": g2_name,
            "group1_pixels": count_g1,
            "group2_pixels": count_g2,
            "reason": (
                f"Insufficient confusable color pairs found "
                f"({g1_name}: {count_g1} px, {g2_name}: {count_g2} px; min required: {min_pixels} px)."
            ),
        }

    # (a) CIELAB means in the simulated original
    lab_sim_orig = rgb_to_lab(simulated_original)
    mean_g1_orig = lab_sim_orig[mask_g1].mean(axis=0)
    mean_g2_orig = lab_sim_orig[mask_g2].mean(axis=0)
    de_sim_orig = float(np.linalg.norm(mean_g1_orig - mean_g2_orig))

    # (b) CIELAB means in the simulated corrected
    lab_sim_corr = rgb_to_lab(simulated_corrected)
    mean_g1_corr = lab_sim_corr[mask_g1].mean(axis=0)
    mean_g2_corr = lab_sim_corr[mask_g2].mean(axis=0)
    de_sim_corr = float(np.linalg.norm(mean_g1_corr - mean_g2_corr))

    if de_sim_orig > 0:
        improvement_pct = ((de_sim_corr - de_sim_orig) / de_sim_orig) * 100.0
    else:
        improvement_pct = 0.0

    return {
        "valid": True,
        "delta_e_simulated_original": round(de_sim_orig, 4),
        "delta_e_simulated_corrected": round(de_sim_corr, 4),
        "improvement_pct": round(improvement_pct, 2),
        "group1_name": g1_name,
        "group2_name": g2_name,
        "group1_pixels": count_g1,
        "group2_pixels": count_g2,
        "interpretation": (
            "Higher delta_e_simulated_corrected indicates improved distinction "
            "between confusable color pairs for the CVD observer."
        ),
    }


def compute_metrics(
    original: np.ndarray,
    simulated: np.ndarray,
    corrected: np.ndarray,
    deficiency: str,
    severity: float,
    region_stats: dict | None = None,
) -> dict:
    """
    Compute and bundle all metrics for the ChromaAssist API response.
    """
    # ΔE between original and its simulation
    # (how much perceptual info is lost through the CVD lens)
    de_original_vs_sim = mean_delta_e(original, simulated)

    # Simulate the corrected image so we can measure how much ΔE is left
    corrected_simulated = simulate(corrected, deficiency, severity)
    de_corrected_vs_sim = mean_delta_e(corrected, corrected_simulated)

    # Compute pair discriminability metric
    pair_discrim = pair_discriminability(
        original=original,
        simulated_original=simulated,
        simulated_corrected=corrected_simulated,
        deficiency=deficiency,
    )

    # Convenience top-level fields for pair discriminability
    pair_orig = pair_discrim.get("delta_e_simulated_original")
    pair_corr = pair_discrim.get("delta_e_simulated_corrected")
    pair_gain = pair_discrim.get("improvement_pct")

    result = {
        "original_vs_simulated_delta_e": round(de_original_vs_sim, 4),
        "corrected_vs_its_simulation_delta_e": round(de_corrected_vs_sim, 4),
        "pair_delta_e_simulated_original": pair_orig,
        "pair_delta_e_simulated_corrected": pair_corr,
        "pair_discriminability_gain_pct": pair_gain,
        "pair_discriminability_note": (
            "Higher pair delta-E indicates that the two confusable colors are easier to tell apart."
        ),
        "information_lost_note": (
            "Whole-image delta-E measures total color information lost across the entire scene (lower is better)."
        ),
        "delta_e_note": (
            "Whole-image delta-E: lower = less information lost. "
            "Pair discriminability delta-E: higher = confusable colors are easier to tell apart."
        ),
        "deficiency": deficiency,
        "severity": severity,
        "pair_discriminability": pair_discrim,
    }

    if region_stats:
        result["region_stats"] = region_stats

    return result
