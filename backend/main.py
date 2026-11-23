"""
main.py
=======
ChromaAssist FastAPI backend.

Endpoints
---------
GET  /api/health    – liveness check
POST /api/process   – single processed image + metrics
POST /api/compare   – four-way comparison + metrics
"""

import io
import base64
import logging
from typing import Literal

import numpy as np
import cv2
from PIL import Image
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from processing.simulation import simulate
from processing.daltonize import daltonize, pseudocolor
from processing.metrics import compute_metrics

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chromaassist")

app = FastAPI(
    title="ChromaAssist API",
    description=(
        "Colourblind-friendly image processing backend. "
        "Simulate CVD, daltonize, and compare images."
    ),
    version="1.0.0",
)

# Allow requests from the Vite dev server (frontend not built yet, but we
# configure CORS now so it works out of the box once Part 2 starts).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024    # 10 MB
MAX_LONGEST_SIDE = 1600                   # pixels – downscale threshold
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _validate_and_load(upload: UploadFile) -> np.ndarray:
    """
    Validate the uploaded file (type + size), read it, decode to uint8 RGB
    NumPy array, and downscale if the longest side exceeds MAX_LONGEST_SIDE.

    Raises HTTPException (400 / 413) with a JSON detail on any error.
    """
    import os

    # --- Content-type check ---
    # Browsers set Content-Type, but it can be spoofed. We check both the
    # MIME type reported by the browser AND the file extension.
    ct = (upload.content_type or "").lower()
    ext = os.path.splitext(upload.filename or "")[1].lower()

    if ct not in ALLOWED_CONTENT_TYPES and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_file_type",
                "message": (
                    f"Only PNG and JPEG images are accepted. "
                    f"Received content-type='{ct}', extension='{ext}'."
                ),
            },
        )

    # --- Read raw bytes ---
    raw = upload.file.read()

    # --- Size check (after reading so we have the true byte count) ---
    if len(raw) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "file_too_large",
                "message": (
                    f"Maximum allowed file size is 10 MB. "
                    f"Uploaded file is {len(raw) / (1024*1024):.2f} MB."
                ),
            },
        )

    # --- Decode image ---
    try:
        pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "image_decode_failed",
                "message": f"Could not decode the uploaded file as an image: {exc}",
            },
        )

    # Secondary extension/magic check using Pillow's format detection
    if pil_img.format and pil_img.format.upper() not in {"PNG", "JPEG"}:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_file_type",
                "message": (
                    f"Only PNG and JPEG images are accepted. "
                    f"Detected format: '{pil_img.format}'."
                ),
            },
        )

    img = np.array(pil_img, dtype=np.uint8)   # (H, W, 3) RGB

    # --- Downscale if needed ---
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest > MAX_LONGEST_SIDE:
        scale = MAX_LONGEST_SIDE / longest
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        # INTER_AREA is best for downscaling (avoids aliasing)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.info("Downscaled image from %dx%d to %dx%d", h, w, new_h, new_w)

    return img


def _to_base64_png(img_uint8: np.ndarray) -> str:
    """
    Encode a uint8 RGB NumPy array as a base64-encoded PNG string.
    The string can be embedded directly in JSON and used as a data-URI
    by the frontend:  <img src="data:image/png;base64,{result}" />
    """
    pil_img = Image.fromarray(img_uint8.astype(np.uint8), mode="RGB")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["health"])
async def health():
    """Liveness check – returns HTTP 200 when the server is up."""
    return {"status": "ok", "service": "ChromaAssist"}


@app.post("/api/process", tags=["processing"])
async def process_image(
    file: UploadFile = File(..., description="PNG or JPEG image, max 10 MB"),
    mode: Literal["simulate", "correct", "pseudocolor"] = Form(
        ..., description="Processing mode"
    ),
    deficiency: Literal["protanopia", "deuteranopia", "tritanopia"] = Form(
        "deuteranopia", description="Type of colour vision deficiency"
    ),
    severity: float = Form(
        1.0, ge=0.0, le=1.0,
        description="CVD severity: 0 = no effect, 1 = full simulation"
    ),
    method: Literal["global", "targeted"] = Form(
        "global", description="Correction method (used only when mode=correct)"
    ),
    colormap: Literal["viridis", "cividis"] = Form(
        "viridis", description="Colormap for pseudo-colour mode"
    ),
):
    """
    Process an uploaded image for colour-vision-deficiency support.

    Returns a JSON object with:
    - **processed_image_b64** : base64-encoded PNG of the result
    - **metrics**             : delta-E scores and optional region stats
    """
    img = _validate_and_load(file)

    region_stats: dict = {}

    if mode == "simulate":
        processed = simulate(img, deficiency, severity)
        simulated = processed
        corrected = processed

    elif mode == "correct":
        corrected, simulated, region_stats = daltonize(
            img, deficiency, severity, method
        )
        processed = corrected

    elif mode == "pseudocolor":
        processed = pseudocolor(img, colormap)
        # For pseudo-colour, simulate the original for metric purposes
        simulated = simulate(img, deficiency, severity)
        corrected = processed

    else:
        raise HTTPException(status_code=400, detail={"error": "invalid_mode"})

    metrics = compute_metrics(
        original=img,
        simulated=simulated,
        corrected=corrected,
        deficiency=deficiency,
        severity=severity,
        region_stats=region_stats if region_stats else None,
    )

    return JSONResponse({
        "processed_image_b64": _to_base64_png(processed),
        "metrics": metrics,
    })


@app.post("/api/compare", tags=["processing"])
async def compare_images(
    file: UploadFile = File(..., description="PNG or JPEG image, max 10 MB"),
    deficiency: Literal["protanopia", "deuteranopia", "tritanopia"] = Form(
        "deuteranopia"
    ),
    severity: float = Form(1.0, ge=0.0, le=1.0),
    method: Literal["global", "targeted"] = Form("global"),
):
    """
    Four-way comparison for a before/after analysis.

    Returns:
    - **original_b64**             : the uploaded image
    - **simulated_b64**            : how a CVD observer sees the original
    - **corrected_b64**            : daltonized original
    - **corrected_simulated_b64**  : how a CVD observer sees the corrected image
    - **metrics**                  : delta-E scores and optional region stats
    """
    img = _validate_and_load(file)

    corrected, simulated, region_stats = daltonize(
        img, deficiency, severity, method
    )

    # Simulate the corrected image to close the comparison loop
    from processing.simulation import simulate as sim_fn
    corrected_simulated = sim_fn(corrected, deficiency, severity)

    metrics = compute_metrics(
        original=img,
        simulated=simulated,
        corrected=corrected,
        deficiency=deficiency,
        severity=severity,
        region_stats=region_stats if region_stats else None,
    )

    return JSONResponse({
        "original_b64":            _to_base64_png(img),
        "simulated_b64":           _to_base64_png(simulated),
        "corrected_b64":           _to_base64_png(corrected),
        "corrected_simulated_b64": _to_base64_png(corrected_simulated),
        "metrics": metrics,
    })
