"""
evaluate.py
===========
ChromaAssist Evaluation & Benchmarking Script.

Iterates over test images in /samples (including Ishihara plates), runs
CVD simulation and daltonization (both global and targeted methods) for
protanopia and deuteranopia at severity 1.0, logs pair discriminability
metrics and whole-image Delta-E metrics, generates a CSV report, prints a
formatted results table, and saves 4-panel side-by-side comparison images
to /evaluation_output.
"""

import os
import sys
import csv
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

# Ensure backend root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from processing.simulation import simulate
from processing.daltonize import daltonize
from processing.metrics import mean_delta_e, pair_discriminability


def create_composite_image(
    original: np.ndarray,
    simulated: np.ndarray,
    corrected: np.ndarray,
    corrected_simulated: np.ndarray,
    deficiency: str,
    method: str,
) -> Image.Image:
    """
    Stitch four images horizontally side-by-side with clear text headers.
    Panels:
      1. Original
      2. Simulated (severity 1.0)
      3. Corrected (method)
      4. Corrected then Simulated
    """
    h, w = original.shape[:2]
    header_h = 40
    padding = 8
    total_w = (w * 4) + (padding * 5)
    total_h = h + header_h + (padding * 2)

    composite = Image.new("RGB", (total_w, total_h), (24, 28, 36))
    draw = ImageDraw.Draw(composite)

    panels = [
        ("1. Original", original, (255, 255, 255)),
        (f"2. Simulated ({deficiency[:4].capitalize()})", simulated, (255, 196, 0)),
        (f"3. Corrected ({method})", corrected, (100, 180, 255)),
        ("4. Corrected + Simulated", corrected_simulated, (110, 235, 130)),
    ]

    for idx, (label, img_arr, label_color) in enumerate(panels):
        x_offset = padding + idx * (w + padding)
        y_offset = padding + header_h

        # Draw panel title
        draw.text(
            (x_offset + 4, padding + 10),
            label,
            fill=label_color,
        )

        # Paste panel image
        pil_panel = Image.fromarray(img_arr.astype(np.uint8), mode="RGB")
        composite.paste(pil_panel, (x_offset, y_offset))

        # Thin border around each image
        draw.rectangle(
            [x_offset - 1, y_offset - 1, x_offset + w, y_offset + h],
            outline=(60, 68, 80),
            width=1,
        )

    return composite


def run_evaluation(samples_dir: Path, output_dir: Path):
    """
    Execute full evaluation suite across all sample images.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect valid images
    valid_exts = {".png", ".jpg", ".jpeg"}
    image_paths = sorted([
        p for p in samples_dir.iterdir()
        if p.is_file() and p.suffix.lower() in valid_exts
    ])

    if not image_paths:
        print(f"[!] No valid PNG/JPEG images found in {samples_dir}")
        return []

    print("=" * 115)
    print(f" ChromaAssist Evaluation: {len(image_paths)} sample(s) found in {samples_dir}")
    print(" Deficiencies: Protanopia, Deuteranopia | Severity: 1.0 | Methods: Global, Targeted")
    print("=" * 115)

    deficiencies = ["protanopia", "deuteranopia"]
    methods = ["global", "targeted"]

    records = []

    for img_path in image_paths:
        try:
            pil_img = Image.open(img_path).convert("RGB")
        except Exception as exc:
            print(f"[!] Could not open image {img_path.name}: {exc}")
            continue

        w, h = pil_img.size
        if max(w, h) > 1200:
            scale = 1200 / max(w, h)
            pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        original = np.array(pil_img, dtype=np.uint8)

        for deficiency in deficiencies:
            simulated = simulate(original, deficiency, severity=1.0)
            de_lost_orig = mean_delta_e(original, simulated)

            for method in methods:
                corrected, _, stats = daltonize(
                    original, deficiency, severity=1.0, method=method
                )

                corrected_simulated = simulate(corrected, deficiency, severity=1.0)
                de_lost_corr = mean_delta_e(corrected, corrected_simulated)

                # Pair discriminability metric
                p_discrim = pair_discriminability(
                    original=original,
                    simulated_original=simulated,
                    simulated_corrected=corrected_simulated,
                    deficiency=deficiency,
                )

                area_pct = stats.get("area_pct", None) if method == "targeted" else 100.0

                record = {
                    "image_name": img_path.name,
                    "deficiency": deficiency,
                    "method": method,
                    "delta_e_lost_orig": round(de_lost_orig, 2),
                    "delta_e_lost_corr": round(de_lost_corr, 2),
                    "pair_discrim_sim_orig": p_discrim["delta_e_simulated_original"],
                    "pair_discrim_sim_corr": p_discrim["delta_e_simulated_corrected"],
                    "pair_discrim_gain_pct": p_discrim["improvement_pct"],
                    "target_mask_area_pct": round(area_pct, 1) if area_pct is not None else None,
                }
                records.append(record)

                # Save side-by-side composite image
                comp_img = create_composite_image(
                    original=original,
                    simulated=simulated,
                    corrected=corrected,
                    corrected_simulated=corrected_simulated,
                    deficiency=deficiency,
                    method=method,
                )
                stem = img_path.stem
                comp_filename = f"{stem}_{deficiency}_{method}.png"
                comp_path = output_dir / comp_filename
                comp_img.save(comp_path, format="PNG")

    # 1. Print formatted console table
    print("\n" + "-" * 115)
    print(
        f"{'Image Name':<22} | {'Deficiency':<12} | {'Method':<8} | "
        f"{'ΔE Lost Orig':<12} | {'ΔE Lost Corr':<12} | "
        f"{'Pair ΔE Orig':<12} | {'Pair ΔE Corr':<12} | {'Pair Gain':<10}"
    )
    print("-" * 115)
    for r in records:
        p_orig_str = f"{r['pair_discrim_sim_orig']:.2f}" if r['pair_discrim_sim_orig'] is not None else "N/A"
        p_corr_str = f"{r['pair_discrim_sim_corr']:.2f}" if r['pair_discrim_sim_corr'] is not None else "N/A"
        gain_str = f"+{r['pair_discrim_gain_pct']:.1f}%" if r['pair_discrim_gain_pct'] is not None and r['pair_discrim_gain_pct'] >= 0 else (
            f"{r['pair_discrim_gain_pct']:.1f}%" if r['pair_discrim_gain_pct'] is not None else "N/A"
        )

        print(
            f"{r['image_name']:<22} | "
            f"{r['deficiency']:<12} | "
            f"{r['method']:<8} | "
            f"{r['delta_e_lost_orig']:>12.2f} | "
            f"{r['delta_e_lost_corr']:>12.2f} | "
            f"{p_orig_str:>12} | "
            f"{p_corr_str:>12} | "
            f"{gain_str:>10}"
        )
    print("-" * 115)

    # 2. Write CSV report
    csv_path = output_dir / "results.csv"
    fieldnames = [
        "image_name",
        "deficiency",
        "method",
        "delta_e_lost_orig",
        "delta_e_lost_corr",
        "pair_discrim_sim_orig",
        "pair_discrim_sim_corr",
        "pair_discrim_gain_pct",
        "target_mask_area_pct",
    ]
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"\n[✓] Results table written to: {csv_path}")
    print(f"[✓] Side-by-side comparison images saved to: {output_dir}")
    print("[✓] Metric Guide:")
    print("    - Pair ΔE: Higher is better (measures contrast between previously confusable red and green regions).")
    print("    - ΔE Lost Info: Lower is better (measures whole-image chromatic deviation from original trichromatic view).")
    print("=" * 115 + "\n")

    return records


def main():
    parser = argparse.ArgumentParser(description="ChromaAssist Image Evaluation Pipeline")
    parser.add_argument(
        "--samples-dir",
        type=str,
        default=None,
        help="Path to directory containing input sample images (default: auto-detected)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Path to directory for comparison outputs & CSV (default: auto-detected)",
    )
    args = parser.parse_args()

    # Auto-resolve paths relative to project root or cwd
    if args.samples_dir:
        samples_dir = Path(args.samples_dir).resolve()
    else:
        candidates = [
            SCRIPT_DIR.parent / "samples",
            Path.cwd() / "samples",
            SCRIPT_DIR / "samples",
        ]
        samples_dir = next((c for c in candidates if c.exists()), candidates[0])

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        candidates = [
            SCRIPT_DIR.parent / "evaluation_output",
            Path.cwd() / "evaluation_output",
            SCRIPT_DIR / "evaluation_output",
        ]
        output_dir = candidates[0]

    run_evaluation(samples_dir, output_dir)


if __name__ == "__main__":
    main()
